# AWS Network Security - Architecture 3-Tiers

## Description

Script Python (boto3) pour déployer une infrastructure réseau AWS sécurisée avec une architecture 3-tiers.

## Architecture
```
Internet
    │
    ▼
┌─────────────────────────────────────────┐
│              VPC 10.0.0.0/16            │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Public Subnets (Web Tier)     │   │
│  │   10.0.1.0/24 | 10.0.2.0/24     │   │
│  │        [NAT Gateway]            │   │
│  └─────────────────────────────────┘   │
│                  │                      │
│  ┌─────────────────────────────────┐   │
│  │   Private Subnets (App Tier)    │   │
│  │   10.0.3.0/24 | 10.0.4.0/24     │   │
│  └─────────────────────────────────┘   │
│                  │                      │
│  ┌─────────────────────────────────┐   │
│  │   Private Subnets (DB Tier)     │   │
│  │   10.0.5.0/24 | 10.0.6.0/24     │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Ressources créées

- 1 VPC
- 6 Subnets (2 publics, 2 app, 2 db)
- 1 Internet Gateway
- 1 NAT Gateway + Elastic IP
- 3 Route Tables
- 3 Security Groups
- 1 Network ACL

## Security Groups

| Tier | Ports | Source |
|------|-------|--------|
| Web | 80, 443, 22 | Internet / Mon IP |
| App | 8080, 22 | Web-Tier-SG |
| DB | 3306 | App-Tier-SG |

## Prérequis

- Python 3.x
- boto3
- AWS CLI configuré

## Installation
```bash
pip install boto3
aws configure
```

## Utilisation
```bash
python infra.py
```

## Nettoyage

Supprimer les ressources dans cet ordre :
1. NAT Gateway
2. Elastic IP
3. Security Groups
4. Route Tables
5. Subnets
6. Internet Gateway
7. VPC

## Auteur

Matthieu - Jedha Cybersecurity Bootcamp
