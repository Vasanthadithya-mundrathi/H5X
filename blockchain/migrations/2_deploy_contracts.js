const H5XHashStorage = artifacts.require("H5XHashStorage");

/**
 * @title Initial Migration
 * @dev Deploy the H5XHashStorage contract
 */
module.exports = function (deployer, network, accounts) {
  console.log("🚀 Deploying H5XHashStorage contract...");
  console.log("Network:", network);
  console.log("Deployer account:", accounts[0]);
  
  return deployer.deploy(H5XHashStorage).then((instance) => {
    console.log("✅ H5XHashStorage deployed at:", instance.address);
    console.log("📝 Contract owner:", accounts[0]);
    
    // Verify deployment by checking contract stats
    return instance.getStats().then((stats) => {
      console.log("📊 Initial stats - Total hashes:", stats.total.toString());
      console.log("👤 Contract owner:", stats.contractOwner);
    });
  });
};