import codecs
import re
from typing import Optional

import ffx
from nrlf.core.errors import InvalidLogicalIdError

_NHS_NO_BLOCK_SIZE = 9
_NHS_CHECK_DIGIT_WEIGHTINGS = [10, 9, 8, 7, 6, 5, 4, 3, 2]
_INVALID_CHECK_DIGIT = 10
_HEX_RADIX = 16
_ALPHA_NUM_RADIX = 36
TOKENISED_LOGICAL_ID_REGEX = re.compile(
    "^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})-([a-f0-9]{20})$"
)


def _is_tokenised_logical_id(logical_id: str) -> Optional[re.Match[str]]:
    return TOKENISED_LOGICAL_ID_REGEX.match(logical_id)


def _is_alphanumeric(char: str) -> bool:
    code = ord(char)
    return (47 < code < 58) or (64 < code < 91)


def _extract_mask(text: str):
    """Generate a mask for each character"""
    mask = []
    alphas = ""
    for char in text:
        if _is_alphanumeric(char):
            alphas += char
            mask.append(None)
        else:
            mask.append(char)

    return alphas, mask


def _apply_mask(alpha_chars, mask):
    """Apply a specified mask to the characters"""
    char_enum = enumerate(alpha_chars)
    for loc in mask:
        if loc is None:
            _, char = next(char_enum)
            yield char
        else:
            yield loc


def _get_tweak_number(length):
    """
    Creates a "tweak value"
    Unsure if this is required for NRL's use case, as it doesn't seem to be used
    """
    return "0".rjust(length, "0")[:length]


def _calculate_nhs_number_check_digit(nhs_number: str):
    digits = [int(num) for num in nhs_number[:9]]

    if len(digits) != 9:
        raise ValueError(
            f"Expected NHS number to have 9 digits - received {nhs_number}"
        )

    check_digit_sum = sum([x * y for x, y in zip(digits, _NHS_CHECK_DIGIT_WEIGHTINGS)])
    check_digit = 11 - (check_digit_sum % 11)

    return 0 if check_digit == 11 else check_digit


def _decrypt_nhs_number(encrypted_nhs_number: str, logical_id_seed: str):
    if len(encrypted_nhs_number) != 10 or encrypted_nhs_number[0] != "X":
        raise ValueError("Invalid Cipher Text")

    key = ffx.FFXInteger(logical_id_seed, radix=_HEX_RADIX, blocksize=32)

    # Discard the leading character
    encrypted_nhs_number = encrypted_nhs_number[-_NHS_NO_BLOCK_SIZE:].upper()

    cipher_alphas, mask = _extract_mask(encrypted_nhs_number)
    len_to_decrypt = len(cipher_alphas)

    tweak_number = _get_tweak_number(len_to_decrypt)
    cipher_number = ffx.FFXInteger(cipher_alphas, radix=_ALPHA_NUM_RADIX)

    ffx_object = ffx.new(key.to_bytes(16), radix=_ALPHA_NUM_RADIX)

    plain_number = ffx_object.decrypt(tweak_number, cipher_number)
    plain_alphas = str(plain_number).upper()

    plain_nhs_number = "".join(_apply_mask(plain_alphas, mask))
    return plain_nhs_number


def decode_tokenised_logical_id(logicalId, logicalIdSeed):
    match = _is_tokenised_logical_id(logicalId)

    if not match:
        raise InvalidLogicalIdError("Logical ID is not a valid tokenised value")

    identifier = match.group(1)
    hex_encoded_encrypted_nhs_number = match.group(2)
    encrypted_nhs_number = codecs.decode(
        hex_encoded_encrypted_nhs_number, "hex"
    ).decode("utf-8")

    nhs_number = _decrypt_nhs_number(encrypted_nhs_number, logicalIdSeed)

    check_digit = _calculate_nhs_number_check_digit(nhs_number)
    if check_digit == _INVALID_CHECK_DIGIT:
        raise ValueError(f"Invalid Check Digit Detokenising: {nhs_number}")

    return identifier, f"{nhs_number}{check_digit}"


def encode_logical_id(logical_id, logical_id_seed, nhs_number: str):
    key = ffx.FFXInteger(logical_id_seed, radix=_HEX_RADIX, blocksize=32)

    nhs_num_without_check_digit = nhs_number[:_NHS_NO_BLOCK_SIZE].upper()
    plain_alphas, mask = _extract_mask(nhs_num_without_check_digit)

    len_to_encrypt = len(plain_alphas)

    tweak_number = _get_tweak_number(len_to_encrypt)
    plain_number = ffx.FFXInteger(plain_alphas, radix=_ALPHA_NUM_RADIX)

    ffx_object = ffx.new(key.to_bytes(16), _ALPHA_NUM_RADIX)

    cipher = ffx_object.encrypt(tweak_number, plain_number)
    cipher_alphas = str(cipher).upper()
    cipher_text = "X" + "".join(_apply_mask(cipher_alphas, mask))
    hex_encoded_cipher_text = codecs.encode(cipher_text.encode("utf-8"), "hex").decode(
        "utf-8"
    )

    return f"{logical_id}-{hex_encoded_cipher_text}"
