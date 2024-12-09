// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract LoyaltyPoints {
    mapping(address => uint256) public pointsBalance;
    mapping(address => bool) public isUserRegistered;

    event PointsIssued(address indexed to, uint256 amount);
    event PointsRedeemed(address indexed from, uint256 amount);
    event PointsTransferred(address indexed from, address indexed to, uint256 amount);
    event UserRegistered(address indexed user); // Event for user registration

    // Optional: Owner of the contract
    address public owner;

    constructor() {
        owner = msg.sender; // Set the contract creator as the owner
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    // Function to register a user
    function registerUser() external {
        require(!isUserRegistered[msg.sender], "User already registered");
        isUserRegistered[msg.sender] = true;
        emit UserRegistered(msg.sender); // Emit an event for logging
    }

    function issuePoints(address to, uint256 amount) external {
        require(isUserRegistered[to], "User not registered");
        pointsBalance[to] += amount;
        emit PointsIssued(to, amount);
    }

    function redeemPoints(uint256 amount) external {
        require(pointsBalance[msg.sender] >= amount, "Insufficient points");
        pointsBalance[msg.sender] -= amount;
        emit PointsRedeemed(msg.sender, amount);
    }

    function transferPoints(address to, uint256 amount) external {
        require(pointsBalance[msg.sender] >= amount, "Insufficient points");
        pointsBalance[msg.sender] -= amount;
        pointsBalance[to] += amount;
        emit PointsTransferred(msg.sender, to, amount);
    }

    // Optional: function to check points balance
    function getPointsBalance(address user) external view returns (uint256) {
        return pointsBalance[user];
    }
}
