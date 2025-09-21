/**
 * @title Truffle Migration Configuration
 * @dev Initial migration script for Truffle framework
 */
const Migrations = artifacts.require("Migrations");

module.exports = function (deployer) {
  deployer.deploy(Migrations);
};