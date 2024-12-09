const LoyaltyPoints = artifacts.require("LoyaltyPoints");

module.exports = function (deployer) {
    deployer.deploy(LoyaltyPoints);
};
