require("source-map-support/register");
const serverlessExpress = require("@vendia/serverless-express/src/index.js");

const app = require("./src/app");

exports.handler = serverlessExpress({ app });
