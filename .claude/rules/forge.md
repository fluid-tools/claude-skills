---
paths: "**/*.sol, foundry.toml"
---

## Abstract Chain Foundry Rules

### ZK Foundry Requirement

Abstract is a ZKsync-based chain. **Always use foundry-zksync** and include the `--zksync` flag for all forge commands.

```bash
# Correct
forge build --zksync
forge test --zksync
forge script --zksync
forge create --zksync

# Wrong (missing --zksync)
forge build
forge test
```

### Chain Configuration

| Property     | Mainnet                      | Testnet                            |
| ------------ | ---------------------------- | ---------------------------------- |
| Name         | Abstract                     | Abstract Testnet                   |
| Chain ID     | 2741                         | 11124                              |
| RPC URL      | https://api.mainnet.abs.xyz  | https://api.testnet.abs.xyz        |
| RPC URL (WS) | wss://api.mainnet.abs.xyz/ws | wss://api.testnet.abs.xyz/ws       |
| Explorer     | https://abscan.org/          | https://sepolia.abscan.org/        |
| Verify URL   | https://api.abscan.org/api   | https://api-sepolia.abscan.org/api |
| Currency     | ETH                          | ETH                                |

### Deployment Commands

```bash
# Deploy to Abstract Testnet
forge script script/Deploy.s.sol --zksync --rpc-url https://api.testnet.abs.xyz --broadcast

# Deploy to Abstract Mainnet
forge script script/Deploy.s.sol --zksync --rpc-url https://api.mainnet.abs.xyz --broadcast

# Verify on Abstract Testnet
forge verify-contract <ADDRESS> <CONTRACT> --zksync --verifier-url https://api-sepolia.abscan.org/api --chain 11124

# Verify on Abstract Mainnet
forge verify-contract <ADDRESS> <CONTRACT> --zksync --verifier-url https://api.abscan.org/api --chain 2741
```

### foundry.toml Configuration

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]

[rpc_endpoints]
abstract_mainnet = "https://api.mainnet.abs.xyz"
abstract_testnet = "https://api.testnet.abs.xyz"

[etherscan]
abstract_mainnet = { key = "${ABSCAN_API_KEY}", url = "https://api.abscan.org/api", chain = 2741 }
abstract_testnet = { key = "${ABSCAN_API_KEY}", url = "https://api-sepolia.abscan.org/api", chain = 11124 }
```
