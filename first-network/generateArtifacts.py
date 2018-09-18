import os
import argparse
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

def genOrdererService(domainName, networkName, loggingLevel):
    config = {
        "orderer": {
            "hostname": "",
            "image": "",
            "environment": [
                "ORDERER_GENERAL_LOGLEVEL={}".format(loggingLevel),
                "ORDERER_GENERAL_LISTENADDRESS=0.0.0.0",
                "ORDERER_GENERAL_GENESISMETHOD=file",
                "ORDERER_GENERAL_GENESISFILE",
                "ORDERER_GENERAL_LOCALMSPID",
                "ORDERER_GENERAL_LOCALMSPDIR",
                "ORDERER_GENERAL_TLS_ENABLED=true",
                "ORDERER_GENERAL_TLS_PRIVATEKEY",
                "ORDERER_GENERAL_TLS_CERTIFICATE",
                "ORDERER_GENERAL_TLS_ROOTCAS",
            ],
            "working_dir": "",
            "command": "orderer",
            "volumes": [
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

def genPeerService(domainName):
    pass

def genCliService(domainName):
    pass

def generateDocker(domainName, orgCount, peerCount):
    config = {
        "version": 3,
        "networks": {
            "hyperledger-ov": {
                "external": True,
            },
        },
        "services": []
    }

    config["services"].append(genOrdererService(domainName, "example.com", "INFO"))

    fHandle = open("docker-compose-cli.yaml", "w")
    fHandle.write(yaml.dump(config, default_flow_style=False))
    fHandle.close()


def generate():
    genCrypto("example.com", 2, [2, 2])
    p = subprocess.Popen(["byfn.sh", "generate"], stdin=subprocess.PIPE, shell=True)
    p.communicate(input=b"y")
    p.wait()

    generateDocker("example.com", 2, [2, 2])

def main():
    parser = argparse.ArgumentParser(os.path.basename(__file__))
    args = parser.parse_args()

    generate()

if __name__ == "__main__":
    main()

