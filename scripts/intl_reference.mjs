// Record what Intl.NumberFormat of this Node build prints, as a reference for the tests.
//
// Writes tests/upstream/intl-node.json (not committed; tests skip while it is absent).
// The tags are every locale of src/indgroup/_cldr.json plus the hand-written probes below,
// each asked for Latin digits (-u-nu-latn). The values are hand-written too. They are
// passed as strings so Intl formats the exact decimal, with as many fraction digits as the
// string has, which is what this library does without rounding.
//
//     node scripts/intl_reference.mjs

import { readFileSync, writeFileSync } from "node:fs";

const root = new URL("..", import.meta.url);
const table = JSON.parse(readFileSync(new URL("src/indgroup/_cldr.json", root), "utf8"));

const PROBES = [
  "en-US", "EN-us", "en-GB", "en-UK", "es-MX", "es-419", "pt-BR", "pt-FR", "de-AT-1996",
  "de-CH-u-co-phonebk", "zh-TW", "zh-SG", "sr-ME", "pa-PK", "iw", "tl", "no", "hi-IN",
];
const VALUES = [
  "0", "7", "-7", "-0", "99", "999", "1000", "1234", "-1234", "12345", "123456", "1234567",
  "-1234567", "12345678", "123456789", "1234567890", "123456789012345678901234567890",
  "0.5", "-0.25", "1234.50", "-9876543.21", "12345.6789", "1000000.000001",
];
const GROUPINGS = ["auto", "min2", "always", false];

function fractionDigits(value) {
  const point = value.indexOf(".");
  return point < 0 ? 0 : value.length - point - 1;
}

const cases = [];
const tags = [...Object.keys(table.locales).filter((tag) => tag !== "und"), ...PROBES];
for (const tag of tags) {
  for (const grouping of GROUPINGS) {
    for (const value of VALUES) {
      const digits = fractionDigits(value);
      let resolved = null;
      let output;
      try {
        const formatter = new Intl.NumberFormat(`${tag.split("-u-")[0]}-u-nu-latn`, {
          useGrouping: grouping,
          minimumFractionDigits: digits,
          maximumFractionDigits: digits,
        });
        resolved = formatter.resolvedOptions().locale.replace(/-u-nu-latn$/, "");
        output = formatter.format(value);
      } catch (error) {
        output = error.name;
      }
      cases.push([tag, grouping === false ? "off" : grouping, value, resolved, output]);
    }
  }
}

const { icu, cldr, unicode, node } = process.versions;
const target = new URL("tests/upstream/intl-node.json", root);
writeFileSync(target, JSON.stringify({ node, icu, cldr, unicode, cases }) + "\n");
console.log(`wrote ${cases.length} cases with Node ${node}, ICU ${icu}, CLDR ${cldr}`);
