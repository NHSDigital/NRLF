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
      executor: "ramping-arrival-rate",
      startRate: 0,
      timeUnit: "1s",
      preAllocatedVUs: 5,
      stages: [
        { target: 10, duration: "5m" },
        { target: 10, duration: "30m" },
        { target: 0, duration: "1m" },
      ],
    },
    readDocumentReference: {
      exec: "readDocumentReference",
      executor: "ramping-arrival-rate",
      startRate: 0,
      timeUnit: "1s",
      preAllocatedVUs: 5,
      stages: [
        { target: 10, duration: "5m" },
        { target: 10, duration: "30m" },
        { target: 0, duration: "1m" },
      ],
    },
    searchDocumentReference: {
      exec: "searchDocumentReference",
      executor: "ramping-arrival-rate",
      startRate: 0,
      timeUnit: "1s",
      preAllocatedVUs: 5,
      stages: [
        { target: 10, duration: "5m" },
        { target: 10, duration: "30m" },
        { target: 0, duration: "1m" },
      ],
    },
    searchPostDocumentReference: {
      exec: "searchPostDocumentReference",
      executor: "ramping-arrival-rate",
      startRate: 0,
      timeUnit: "1s",
      preAllocatedVUs: 5,
      stages: [
        { target: 10, duration: "5m" },
        { target: 10, duration: "30m" },
        { target: 0, duration: "1m" },
      ],
    },
  },
};
