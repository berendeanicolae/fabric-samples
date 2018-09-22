#!/usr/bin/python3
import os
import argparse
import shutil
import subprocess
import yaml

from collections import OrderedDict


def genOrdererConfig(domainName):
    config = []
    config.append({
        "Name": "Orderer",
        "Domain": domainName,
        "Specs": [
            {"Hostname": "orderer"},
        ],
    })

    return config

def genPeerConfig(domainName, orgCount, peerCount):
    config = []

    for org in range(orgCount):
        nodeConfig = {
            "Count": peerCount[org]
        }
        tempConfig = {
            "Name": "Org{}".format(org),
            "Domain": "org{}.{}".format(org+1, domainName),
            "Template": nodeConfig,
            "EnableNodeOUs": True,
            "Users" : {
                "Count": 1
            },
        }

        config.append(tempConfig)

    return config

def genCrypto(domainName, orgCount, peerCount):
    config = {}

    config["OrdererOrgs"] = genOrdererConfig(domainName)
    config["PeerOrgs"] = genPeerConfig(domainName, orgCount, peerCount)

    fHandle = open("crypto-config.yaml", "w")
    fHandle.write(yaml.dump(config, default_flow_style=False))
    fHandle.close()

def genOrdererService(imageName, networkName, domainName, loggingLevel):
    config = {
        "orderer": {
            "hostname": "orderer.{}".format(domainName),
            "image": imageName,
            "environment": [
                "ORDERER_GENERAL_LOGLEVEL={}".format(loggingLevel),
                "ORDERER_GENERAL_LISTENADDRESS=0.0.0.0",
                "ORDERER_GENERAL_GENESISMETHOD=file",
                "ORDERER_GENERAL_GENESISFILE=/var/hyperledger/orderer/orderer.genesis.block",
                "ORDERER_GENERAL_LOCALMSPID=OrdererMSP",
                "ORDERER_GENERAL_LOCALMSPDIR=/var/hyperledger/orderer/msp",
                "ORDERER_GENERAL_TLS_ENABLED=true",
                "ORDERER_GENERAL_TLS_PRIVATEKEY=/var/hyperledger/orderer/tls/server.key",
                "ORDERER_GENERAL_TLS_CERTIFICATE=/var/hyperledger/orderer/tls/server.crt",
                "ORDERER_GENERAL_TLS_ROOTCAS=[/var/hyperledger/orderer/tls/ca.crt]",
            ],
            "working_dir": "/opt/gopath/src/github.com/hyperledger/fabric",
            "command": "orderer",
            "volumes": [
                "/shared/channel-artifacts/genesis.block:/var/hyperledger/orderer/orderer.genesis.block",
                "/shared/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp:/var/hyperledger/orderer/msp",
                "/shared/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/tls/:/var/hyperledger/orderer/tls",
            ],
            "networks": {
                networkName: {
                    "aliases": [
                        "orderer.{}".format(domainName)
                    ],
                }
            }
        }
    }
    return config

def genPeerService(imageName, networkName, domainName, orgIndex, peerIndex, loggingLevel):
    config = {
        "peer{}_org{}".format(peerIndex, orgIndex): {
            "hostname": "peer{}.org{}.{}".format(peerIndex, orgIndex, domainName),
            "image": imageName,
            "environment": [
                "CORE_PEER_ID=peer{}.org{}.{}".format(peerIndex, orgIndex, domainName),
                "CORE_PEER_ADDRESS=peer{}.org{}.{}:7051".format(peerIndex, orgIndex, domainName),
                "CORE_PEER_GOSSIP_BOOTSTRAP=peer{}.org{}.{}:7051".format(0 if peerIndex!=0 else 1, orgIndex, domainName),
                "CORE_PEER_GOSSIP_EXTERNALENDPOINT=peer{}.org{}.{}:7051".format(peerIndex, orgIndex, domainName),
                "CORE_PEER_LOCALMSPID=Org{}MSP".format(orgIndex),
                "CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock",
                "CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=hyperledger-ov",
                "CORE_LOGGING_LEVEL={}".format(loggingLevel),
                "CORE_PEER_TLS_ENABLED=true",
                "CORE_PEER_GOSSIP_USELEADERELECTION=true",
                "CORE_PEER_GOSSIP_ORGLEADER=false",
                "CORE_PEER_PROFILE_ENABLED=true",
                "CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt",
                "CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key",
                "CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            ],
            "working_dir": "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            "command": "peer node start",
            "volumes": [
                "/var/run/:/host/var/run/",
                "/shared/crypto-config/peerOrganizations/org{org}.{domain}/peers/peer{peer}.org{org}.{domain}/msp:/etc/hyperledger/fabric/msp".format(peer=peerIndex, org=orgIndex, domain=domainName),
                "/shared/crypto-config/peerOrganizations/org{org}.{domain}/peers/peer{peer}.org{org}.{domain}/tls:/etc/hyperledger/fabric/tls".format(peer=peerIndex, org=orgIndex, domain=domainName)
            ],
            "networks": {
                networkName: {
                    "aliases": [
                        "peer{}.org{}.{}".format(peerIndex, orgIndex, domainName),
                    ],
                }
            },
        },
    }
    return config

def genCliService(imageName, networkName, domainName, loggingLevel):
    config = {
        "cli" : {
            "image": imageName,
            "environment": [
                  "GOPATH=/opt/gopath",
                  "CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock",
                  "CORE_LOGGING_LEVEL={}".format(loggingLevel),
                  "CORE_PEER_ID=cli",
                  "CORE_PEER_ADDRESS=peer0.org1.example.com:7051",
                  "CORE_PEER_LOCALMSPID=Org1MSP",
                  "CORE_PEER_TLS_ENABLED=true",
                  "CORE_PEER_TLS_CERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/server.crt",
                  "CORE_PEER_TLS_KEY_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/server.key",
                  "CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt",
                  "CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp",
            ],
            "working_dir": "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            "command": "sleep 1d",
            "volumes": [
                "/var/run/:/host/var/run/",
                "/shared/chaincode/:/opt/gopath/src/github.com/chaincode",
                "/shared/crypto-config:/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/",
                "/shared/scripts:/opt/gopath/src/github.com/hyperledger/fabric/peer/scripts/",
                "/shared/channel-artifacts:/opt/gopath/src/github.com/hyperledger/fabric/peer/channel-artifacts",
            ],
            "networks": {
                networkName: {
                    "aliases": [
                        "cli",
                    ],
                }
            },
        }
    }
    return config

def generateDocker(repoOwner, networkName, domainName, orgCount, peerCount, loggingLevel):
    config = {
        "version": '3',
        "networks": {
            networkName: {
                "external": True,
            },
        },
        "services": []
    }

    config["services"].append(genOrdererService("{}/fabric-orderer:latest".format(repoOwner), networkName, domainName, loggingLevel))
    for org in range(orgCount):
        for peer in range(peerCount[org]):
            config["services"].append(genPeerService("{}/fabric-peer:latest".format(repoOwner), networkName, domainName, org+1, peer, loggingLevel))
    config["services"].append(genCliService("{}/fabric-tools:latest".format(repoOwner), networkName, domainName, loggingLevel))

    fHandle = open("docker-compose-cli.yaml", "w")
    fHandle.write(yaml.dump(config, default_flow_style=False))
    fHandle.close()


def generate():
    genCrypto("example.com", 2, [2, 2])
    p = subprocess.Popen(["./byfn.sh generate"], stdin=subprocess.PIPE, cwd=os.getcwd(), shell=True)
    p.communicate(input=b"y")
    p.wait()

    generateDocker("hyperledger", "hyperledger-ov", "example.com", 2, [2, 2], "INFO")

def copytree(src, dst):
    if os.path.isdir(dst): shutil.rmtree(dst)
    shutil.copytree(src, dst)

def deploy():
    if os.path.isdir("/export"):
        copytree("./scripts", "/export/scripts")
        copytree("./crypto-config", "/export/crypto-config")
        copytree("./channel-artifacts", "/export/channel-artifacts")
        copytree("./../chaincode", "/export/chaincode")

        subprocess.Popen(["chmod -R 777 /export"], shell=True).wait()

def main():
    parser = argparse.ArgumentParser(os.path.basename(__file__))
    args = parser.parse_args()

    generate()
    deploy()

if __name__ == "__main__":
    main()
