export function generateNHSNumber() {
  const numberWithoutChecksum = Math.floor(Math.random() * 100000000000)
    .toString()
    .substring(0, 9);
  const remainder =
    numberWithoutChecksum
      .split("")
      .map((digit, index) => {
        return digit * (11 - (index + 1));
      })
      .reduce((acc, curr) => acc + curr, 0) % 11;

  const checkDigit = 11 - remainder;
  if (checkDigit === 11) {
    return `${numberWithoutChecksum}0`;
  }

  return `${numberWithoutChecksum}${checkDigit}`;
}
