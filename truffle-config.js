module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",  // Localhost for Ganache
      port: 7545,         // Port for Ganache
      network_id: "*",    // Match any network id
    },
  },
  compilers: {
    solc: {
      version: "0.8.0",   // Solidity version
    },
  },
};
