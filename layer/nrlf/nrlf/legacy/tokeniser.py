import codecs
import re
from math import prod

import ffx

from nrlf.core.errors import InvalidLogicalIdError

_LOGICAL_ID_BLOCK_SIZE = 32
_NHS_CHECK_DIGIT_WEIGHTINGS = [10, 9, 8, 7, 6, 5, 4, 3, 2]
_INVALID_CHECK_DIGIT = 10
_HEX_RADIX = 16
_ALPHA_NUM_RADIX = 36
TOKENISED_LOGICAL_ID_REGEX = re.compile(
    "^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})-([a-f0-9]{20})$"
)
ENCRYPTED_NHS_START_CHAR = "X"


def _extract_logical_id_components(logical_id: str) -> tuple[str, str]:
    try:
        return TOKENISED_LOGICAL_ID_REGEX.match(logical_id).groups()
    except:
        raise InvalidLogicalIdError("Logical ID is not a valid tokenised value")


def _extract_mask(text: str) -> tuple:
    mask = []
    alphas = ""
    for char in text:
        if char.isalnum():
            alphas += char
            mask.append(None)
        else:
            mask.append(char)
    return alphas, mask


def _apply_mask(alpha_chars: list[str], mask: list[any]) -> str:
    char = iter(alpha_chars)
    return "".join(loc if loc is not None else next(char) for loc in mask)


def _get_tweak_number(length: int) -> str:
    return "0".rjust(length, "0")[:length]


def _calculate_check_digit(nhs_number: str) -> str:
    digits = map(int, nhs_number)
    check_digit_sum = sum(map(prod, zip(digits, _NHS_CHECK_DIGIT_WEIGHTINGS)))
    check_digit = 11 - (check_digit_sum % 11)
    check_digit = 0 if check_digit == 11 else check_digit
    if check_digit == _INVALID_CHECK_DIGIT:
        raise InvalidLogicalIdError(f"Invalid Check Digit for: {nhs_number}")
    return str(check_digit)


def _crypt_nhs_number(nhs_number: str, seed: str, encrypt: bool = True) -> str:
    key = ffx.FFXInteger(seed, radix=_HEX_RADIX, blocksize=_LOGICAL_ID_BLOCK_SIZE)
    ffx_object = ffx.new(key.to_bytes(_HEX_RADIX), radix=_ALPHA_NUM_RADIX)

    truncation = slice(None, -1) if encrypt else slice(1, None)
    truncated_nhs_number = nhs_number[truncation].upper()

    alphas, mask = _extract_mask(truncated_nhs_number)
    tweak_number = _get_tweak_number(length=len(alphas))
    cipher_number = ffx.FFXInteger(alphas, radix=_ALPHA_NUM_RADIX)

    crypter = ffx_object.encrypt if encrypt else ffx_object.decrypt
    crypted_number = crypter(tweak_number, cipher_number)
    alphas = str(crypted_number).upper()

    crypted_nhs_number = _apply_mask(alphas, mask)

    if encrypt:
        crypted_nhs_number = (ENCRYPTED_NHS_START_CHAR + crypted_nhs_number).encode()
    else:
        check_digit = _calculate_check_digit(crypted_nhs_number)
        crypted_nhs_number = crypted_nhs_number + check_digit
    return crypted_nhs_number


def decode_tokenised_id(tokenised_id: str, seed: str) -> tuple:
    logical_id, encoded_nhs_num = _extract_logical_id_components(tokenised_id)
    encrypted_nhs_number = codecs.decode(encoded_nhs_num, "hex").decode()
    nhs_number = _crypt_nhs_number(
        nhs_number=encrypted_nhs_number, seed=seed, encrypt=False
    )
    return (logical_id, nhs_number)


def encode_logical_id(logical_id: str, nhs_number: str, seed: str) -> tuple:
    encrypted_nhs_number = _crypt_nhs_number(
        nhs_number=nhs_number, seed=seed, encrypt=True
    )
    encoded_nhs_num = codecs.encode(encrypted_nhs_number, "hex").decode()
    tokenised_id = f"{logical_id}-{encoded_nhs_num}"
    return tokenised_id
