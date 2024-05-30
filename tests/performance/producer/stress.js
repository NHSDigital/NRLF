export * from "./client.js";

/*
 * NOTE - To run the producer K6 tests, you need to prepare the data by setting
 * the output_full_pointers flag to true in the environment.py:setup() method.
 */

export const options = {
  tlsAuth: [
    {
      cert: open(`../../../truststore/client/${__ENV.ENV_TYPE}.crt`),
      key: open(`../../../truststore/client/${__ENV.ENV_TYPE}.key`),
    },
  ],
  scenarios: {
    createDocumentReference: {
      exec: "createDocumentReference",
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
    updateDocumentReference: {
      exec: "updateDocumentReference",
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { target: 10, duration: "30s" },
        { target: 10, duration: "1m" },
      ],
    },
    deleteDocumentReference: {
      exec: "deleteDocumentReference",
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { target: 10, duration: "30s" },
        { target: 10, duration: "1m" },
      ],
    },
    upsertDocumentReference: {
      exec: "upsertDocumentReference",
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { target: 10, duration: "30s" },
        { target: 10, duration: "1m" },
      ],
    },
  },
};
