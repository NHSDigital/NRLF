"use strict";

const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");
const express = require("express");
const swaggerUi = require("swagger-ui-express");

const rawProducer = fs.readFileSync(
  path.join(__dirname, "..", "api", "nrl-producer-api.yaml"),
  "utf8"
);
const rawConsumer = fs.readFileSync(
  path.join(__dirname, "..", "api", "nrl-consumer-api.yaml"),
  "utf8"
);
const oasProducer = yaml.load(rawProducer);
const oasConsumer = yaml.load(rawConsumer);

const app = express();
var options = {
  explorer: true,
  swaggerOptions: {
    urls: [
      {
        url: "/api/producer/swagger.json",
        name: "NRL Producer API",
      },
      {
        url: "/api/consumer/swagger.json",
        name: "NRL Consumer API",
      },
    ],
  },
};
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(null, options));
app.get("/api/producer/swagger.json", (req, res) => res.json(oasProducer));
app.get("/api/consumer/swagger.json", (req, res) => res.json(oasConsumer));
app.use((req, res) =>
  res.status(404).json({ message: "Not Found", path: req.path })
);
module.exports = app;
