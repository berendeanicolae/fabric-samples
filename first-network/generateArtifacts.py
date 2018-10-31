#!/usr/bin/python3
import os
import argparse
import shutil
import subprocess
import yaml

from collections import OrderedDict

def genNetwork(domainName, orgsCount):
    config = {}

    config

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

def genPeerConfig(domainName, orgsCount, peerCount):
    config = []

    for org in range(orgsCount):
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

def genCrypto(domainName, orgsCount, peerCount):
    config = {}

    config["OrdererOrgs"] = genOrdererConfig(domainName)
    config["PeerOrgs"] = genPeerConfig(domainName, orgsCount, peerCount)

    fHandle = open("crypto-config.yaml", "w")
    fHandle.write(yaml.dump(config, default_flow_style=False))
    fHandle.close()

def genOrdererService(imageName, networkName, domainName, loggingLevel):
    serviceName = "orderer"
    serviceConfig = {
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

    return { serviceName : serviceConfig }

def genPeerService(imageName, networkName, domainName, orgIndex, peerIndex, loggingLevel):
    serviceName = "peer{}_org{}".format(peerIndex, orgIndex)
    serviceConfig = {
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
    }

    return { serviceName : serviceConfig }

def genCliService(imageName, networkName, domainName, loggingLevel):
    serviceName = "cli"
    serviceConfig = {
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
            "/shared/chaincode/:/opt/gopath/src/github.com/hyperledger/fabric/examples/chaincode/go",
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

    return { serviceName : serviceConfig }

def generateDocker(repoOwner, networkName, domainName, orgsCount, peerCount, loggingLevel):
    config = {
        "version": '3',
        "networks": {
            networkName: {
                "external": True,
            },
        },
        "services": {}
    }

    config["services"].update(genOrdererService("{}/fabric-orderer:latest".format(repoOwner), networkName, domainName, loggingLevel))
    for org in range(orgsCount):
        for peer in range(peerCount[org]):
            config["services"].update(genPeerService("berendeanicolae/fabric-peer:latest".format(repoOwner), networkName, domainName, org+1, peer, loggingLevel))
    config["services"].update(genCliService("{}/fabric-tools:latest".format(repoOwner), networkName, domainName, loggingLevel))

    fHandle = open("docker-compose-cli.yaml", "w")
    fHandle.write(yaml.dump(config, default_flow_style=False))
    fHandle.close()

def genNetworkOrgs(domainName, orgsCount):
    config = []
    config.append({
        "Name" : "OrdererOrg",
        "ID" : "OrdererMSP",
        "MSPDir" : "crypto-config/ordererOrganizations/example.com/msp",
    })
    for org in range(orgsCount):
        orgConfig = {}
        orgConfig["Name"] = "Org{}MSP".format(org+1)
        orgConfig["ID"] = "Org{}MSP".format(org+1)
        orgConfig["MSPDir"] = "crypto-config/peerOrganizations/org{}.example.com/msp".format(org+1)
        orgConfig["AnchorPeers"] = [{
            "Host": "peer0.org{}.{}".format(org+1, domainName),
            "Port": 7051,
        }]
        config.append(orgConfig)

    return config

def genNetworkCapabilities():
    config = {}
    config["Global"] = {"V1_1": True}
    config["Orderer"] = {"V1_1": True}
    config["Application"] = {"V1_2": True}

    return config

def genNetworkApplication():
    config = {}
    config["Organizations"] = None

    return config

def genNetworkOrderer(domainName):
    config = {}
    config["OrdererType"] = "solo"
    config["Addresses"] = ["orderer.{}:7050".format(domainName)]
    config["BatchTimeout"] = "2s"
    config["BatchSize"] = {
        "MaxMessageCount": 10,
        "AbsoluteMaxBytes": "99 MB",
        "PreferredMaxBytes": "512 KB",
    }
    config["Kafka"] = {
        "Brokers": ["127.0.0.1:9092"]
    }
    config["Organizations"] = None

    return config

def setNetworkProfiles(config, domainName):
    config["Profiles"] = {}

    config["Profiles"]["TwoOrgsOrdererGenesis"] = {
        "Capabilities": {
            "V1_1": True,
        },
        "Orderer": {
            "OrdererType": config["Orderer"]["OrdererType"],
            "Addresses": config["Orderer"]["Addresses"],
            "BatchTimeout": config["Orderer"]["BatchTimeout"],
            "BatchSize": config["Orderer"]["BatchSize"],
            "Kafka": config["Orderer"]["Kafka"],
            "Organizations": [org for org in config["Organizations"] if "Orderer" in org["ID"]],
            "Capabilities": {
                "V1_1": True
            }
        },
        "Consortiums": {
            "SampleConsortium": {
                "Organizations": [org for org in config["Organizations"] if "Org" in org["ID"]]
            },
        },
    }
    config["Profiles"]["TwoOrgsChannel"] = {
        "Consortium": "SampleConsortium",
        "Application": {
            "Organizations": [org for org in config["Organizations"] if "Org" in org["ID"]],
            "Capabilities": {
                "V1_2": True,
            }
        }
    }

def genNetwork(domainName, orgsCount):
    config = {}

    config["Organizations"] = genNetworkOrgs(domainName, orgsCount)
    config["Capabilities"] = genNetworkCapabilities()
    config["Application"] = genNetworkApplication()
    config["Orderer"] = genNetworkOrderer(domainName)
    setNetworkProfiles(config, domainName)

    fHandle = open("configtx.yaml", "w")
    fHandle.write(yaml.dump(config, default_flow_style=False))
    fHandle.close()

def generate():
    domainName = "example.com"
    orgsCount = 3
    peerCounts = [2, 2, 2]

    genNetwork(domainName, orgsCount)
    genCrypto(domainName, orgsCount, peerCounts)
    p = subprocess.Popen(["./byfn.sh generate"], stdin=subprocess.PIPE, cwd=os.getcwd(), shell=True)
    p.communicate(input=b"y")
    p.wait()

    generateDocker("hyperledger", "hyperledger-ov", domainName, orgsCount, peerCounts, "INFO")

def copytree(src, dst):
    if os.path.isdir(dst): shutil.rmtree(dst)
    shutil.copytree(src, dst)

def deploy():
    if os.path.isdir("/export"):
        copytree("./../high-throughput/scripts", "/export/scripts")
        copytree("./crypto-config", "/export/crypto-config")
        copytree("./channel-artifacts", "/export/channel-artifacts")
        copytree("./../high-throughput/chaincode", "/export/chaincode")

        subprocess.Popen(["chmod -R 777 /export"], shell=True).wait()

def main():
    parser = argparse.ArgumentParser(os.path.basename(__file__))
    args = parser.parse_args()

    generate()
    deploy()

if __name__ == "__main__":
    main()
