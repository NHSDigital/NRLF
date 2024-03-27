export * from "./client.js";

export const options = {
  tlsAuth: [
    {
      cert: open(`../../../truststore/client/${__ENV.ENV_TYPE}.crt`),
      key: open(`../../../truststore/client/${__ENV.ENV_TYPE}.key`),
    },
  ],
  scenarios: {
    countDocumentReference: {
      exec: "countDocumentReference",
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { target: 10, duration: "30s" },
        { target: 10, duration: "1m" },
      ],
    },
    readDocumentReference: {
      exec: "readDocumentReference",
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { target: 10, duration: "30s" },
        { target: 10, duration: "1m" },
      ],
    },
    searchDocumentReference: {
      exec: "searchDocumentReference",
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { target: 10, duration: "30s" },
        { target: 10, duration: "1m" },
      ],
    },
    searchPostDocumentReference: {
      exec: "searchPostDocumentReference",
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { target: 10, duration: "30s" },
        { target: 10, duration: "1m" },
      ],
    },
  },
};
