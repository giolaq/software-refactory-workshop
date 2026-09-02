const minimum = [22, 13, 0];
const actual = process.versions.node.split(".").map((part) => Number.parseInt(part, 10));

const comparison = actual.reduce(
  (result, part, index) => result || part - minimum[index],
  0,
);
const supported = comparison >= 0;

if (!supported) {
  console.error(
    `Software (re)-Factory workshop guide requires Node.js 22.13.0 or later; found ${process.versions.node}.`,
  );
  console.error("Install a supported Node.js version, run `node --version`, then repeat the command.");
  process.exit(1);
}

console.log(`Node.js ${process.versions.node} satisfies the workshop guide requirement.`);
