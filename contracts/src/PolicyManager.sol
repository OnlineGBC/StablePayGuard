// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title PolicyManager
/// @notice On-chain spending policy enforcement for AI payment agents.
///         Operators define per-agent budgets and limits; agents execute
///         payments only within those bounds.
contract PolicyManager {

    // -----------------------------------------------------------------------
    // Data structures
    // -----------------------------------------------------------------------

    struct Policy {
        address agent;
        address token;          // address(0) = native ETH
        uint256 totalBudget;    // maximum lifetime spend (wei / token units)
        uint256 perTxLimit;     // maximum single-transaction amount
        uint256 validFrom;      // unix timestamp: policy activation
        uint256 validUntil;     // unix timestamp: policy expiry
        bytes32 purposeHash;    // keccak256 of purpose string
        bool    active;
        uint256 spentAmount;    // running total of approved spend
    }

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------

    address public owner;
    uint256 public policyCount;

    mapping(uint256 => Policy) public policies;
    mapping(address => uint256[]) public agentPolicies;

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------

    event PolicyCreated(
        uint256 indexed policyId,
        address indexed agent,
        address token,
        uint256 totalBudget
    );

    event PolicyDeactivated(uint256 indexed policyId);

    event PaymentApproved(
        uint256 indexed policyId,
        address indexed agent,
        uint256 amount,
        uint256 totalSpent
    );

    // -----------------------------------------------------------------------
    // Modifiers
    // -----------------------------------------------------------------------

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------

    constructor() {
        owner = msg.sender;
    }

    // -----------------------------------------------------------------------
    // Policy management
    // -----------------------------------------------------------------------

    /// @notice Create a new spending policy for an AI agent.
    function createPolicy(
        address agent,
        address token,
        uint256 totalBudget,
        uint256 perTxLimit,
        uint256 validFrom,
        uint256 validUntil,
        bytes32 purposeHash,
        bool    active
    ) external onlyOwner returns (uint256 policyId) {
        require(agent != address(0),    "Invalid agent");
        require(totalBudget > 0,        "Budget must be > 0");
        require(perTxLimit <= totalBudget, "Per-tx limit exceeds budget");
        require(validUntil > validFrom, "Invalid time window");

        policyId = ++policyCount;

        policies[policyId] = Policy({
            agent:        agent,
            token:        token,
            totalBudget:  totalBudget,
            perTxLimit:   perTxLimit,
            validFrom:    validFrom,
            validUntil:   validUntil,
            purposeHash:  purposeHash,
            active:       active,
            spentAmount:  0
        });

        agentPolicies[agent].push(policyId);

        emit PolicyCreated(policyId, agent, token, totalBudget);
    }

    /// @notice Approve a payment against a policy. Reverts if any rule is violated.
    function approvePayment(uint256 policyId, uint256 amount)
        external
        returns (bool)
    {
        Policy storage p = policies[policyId];

        require(p.active,                           "Policy inactive");
        require(msg.sender == p.agent,              "Not policy agent");
        require(block.timestamp >= p.validFrom,     "Policy not yet active");
        require(block.timestamp <= p.validUntil,    "Policy expired");
        require(amount <= p.perTxLimit,             "Exceeds per-tx limit");
        require(p.spentAmount + amount <= p.totalBudget, "Budget exhausted");

        p.spentAmount += amount;

        emit PaymentApproved(policyId, msg.sender, amount, p.spentAmount);
        return true;
    }

    /// @notice Deactivate a policy immediately.
    function deactivatePolicy(uint256 policyId) external onlyOwner {
        policies[policyId].active = false;
        emit PolicyDeactivated(policyId);
    }

    // -----------------------------------------------------------------------
    // Views
    // -----------------------------------------------------------------------

    function getPolicy(uint256 policyId) external view returns (
        address agent,
        address token,
        uint256 totalBudget,
        uint256 perTxLimit,
        uint256 validFrom,
        uint256 validUntil,
        bytes32 purposeHash,
        bool    active,
        uint256 spentAmount
    ) {
        Policy storage p = policies[policyId];
        return (
            p.agent, p.token, p.totalBudget, p.perTxLimit,
            p.validFrom, p.validUntil, p.purposeHash, p.active, p.spentAmount
        );
    }

    function getAgentPolicies(address agent) external view returns (uint256[] memory) {
        return agentPolicies[agent];
    }

    function remainingBudget(uint256 policyId) external view returns (uint256) {
        Policy storage p = policies[policyId];
        return p.totalBudget - p.spentAmount;
    }
}
