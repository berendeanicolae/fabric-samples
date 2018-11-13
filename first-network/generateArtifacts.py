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

def genOrdererConfig(domainName, orderersCount):
    config = []
    config.append({
        "Name": "Orderer",
        "Domain": domainName,
        "Specs": [{"Hostname": "orderer{}".format(e)} for e in range(orderersCount)],
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

def genCrypto(domainName, orgsCount, orderersCount, peerCount):
    config = {}

    config["OrdererOrgs"] = genOrdererConfig(domainName, orderersCount)
    config["PeerOrgs"] = genPeerConfig(domainName, orgsCount, peerCount)

    fHandle = open("crypto-config.yaml", "w")
    fHandle.write(yaml.dump(config, default_flow_style=False))
    fHandle.close()

def genZookeperService(imageName, networkName, domainName, zooKeepersCount, index):
    serviceName = "zookeper{}".format(index)
    serviceConfig = {
        "hostname": "zookeper{}.{}".format(index, domainName),
        "image": imageName,
        "networks": {
            networkName: {
                "aliases": [
                    "zookeper{}.{}".format(index, domainName),
                ],
            }
        },
        "environment": [
            "CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE={}".format(networkName),
            "ZOO_MY_ID={}".format(index+1),
            "ZOO_SERVERS={}".format(" ".join(["server.{}=zookeeper{}:2888:3888".format(e+1, e) for e in range(zooKeepersCount)]))
        ],
    }

    return { serviceName : serviceConfig }

def genKafkaService(imageName, networkName, domainName, zooKeepersCount, index):
    serviceName = "kafka{}".format(index)
    serviceConfig = {
        "hostname": "kafka{}.{}".format(index, domainName),
        "image": imageName,
        "networks": {
            networkName: {
                "aliases": [
                    "kafka{}.{}".format(index, domainName),
                ],
            }
        },
        "environment": [
            "CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE={}".format(domainName),
            "KAFKA_MESSAGE_MAX_BYTES={}".format(15728640),
            "KAFKA_REPLICA_FETCH_MAX_BYTES={}".format(15728640),
            "KAFKA_UNCLEAN_LEADER_ELECTION_ENABLE={}".format(False),
            "KAFKA_DEFAULT_REPLICATION_FACTOR={}".format(3),
            "KAFKA_MIN_INSYNC_REPLICAS={}".format(2),
            "KAFKA_ZOOKEEPER_CONNECT={}".format("zookeeper{}.{}:2181".format(e, domainName) for e in range(zooKeepersCount)),
            "KAFKA_BROKER_ID={}".format(index),
            "KAFKA_LOG_RETENTIONMS={}".format(-1),
        ],
    }

    return { serviceName : serviceConfig }


def genOrdererService(imageName, networkName, domainName, loggingLevel, index, kafka=False):
    serviceName = "orderer"
    serviceConfig = {
        "hostname": "orderer{}.{}".format(index, domainName),
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
                    "orderer{}.{}".format(index, domainName)
                ],
            }
        }
    }
    if kafka:
        serviceConfig["environment"].append("ORDERER_KAFKA_RETRY_SHORTINTERVAL=1s")
        serviceConfig["environment"].append("ORDERER_KAFKA_RETRY_SHORTTOTAL=30s")
        serviceConfig["environment"].append("ORDERER_KAFKA_VERBOSE=true")

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

def generateDocker(repoOwner, networkName, domainName, orgsCount, orderersCount, peerCounts, zooKeepersCount, kafkasCount, loggingLevel):
    config = {
        "version": '3',
        "networks": {
            networkName: {
                "external": True,
            },
        },
        "services": {}
    }

    for orderer in range(orderersCount):
        config["services"].update(genOrdererService("{}/fabric-orderer:latest".format(repoOwner), networkName, domainName, loggingLevel, orderer, kafkasCount>0))
    for org in range(orgsCount):
        for peer in range(peerCounts[org]):
            config["services"].update(genPeerService("berendeanicolae/fabric-peer:latest".format(repoOwner), networkName, domainName, org+1, peer, loggingLevel))
    for zooKeeper in range(zooKeepersCount):
        config["services"].update(genZookeperService("{}/fabric-zookeeper:latest".format(repoOwner), networkName, domainName, zooKeepersCount, zooKeeper))
    for kafka in range(kafkasCount):
        config["services"].update(genKafkaService("{}/fabric-kafka:latest".format(repoOwner), networkName, domainName, zooKeepersCount, kafka))
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

def genNetworkOrderer(domainName, orderersCount=1, kafkasCount=0):
    config = {}
    config["OrdererType"] = "solo"
    config["Addresses"] = ["orderer{}.{}:7050".format(e, domainName) for e in range(orderersCount)]
    config["BatchTimeout"] = "2s"
    config["BatchSize"] = {
        "MaxMessageCount": 10,
        "AbsoluteMaxBytes": 10485760,
        "PreferredMaxBytes": 524288,
    }
    config["Kafka"] = {
        "Brokers": ["127.0.0.1:9092"]
    }
    config["Organizations"] = None

    if kafkasCount>0:
        config["OrdererType"] = "kafka"
        config["Kafka"]["Brokers"] = ["kafka{}.{}".format(e, domainName) for e in range(kafkasCount)]

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

def genNetwork(domainName, orgsCount, orderersCount):
    config = {}

    config["Organizations"] = genNetworkOrgs(domainName, orgsCount)
    config["Capabilities"] = genNetworkCapabilities()
    config["Application"] = genNetworkApplication()
    config["Orderer"] = genNetworkOrderer(domainName, orderersCount)
    setNetworkProfiles(config, domainName)

    fHandle = open("configtx.yaml", "w")
    fHandle.write(yaml.dump(config, default_flow_style=False))
    fHandle.close()

def generateHighThroughput(domainName, orgsCount, peersCount):
    fHandle = open("../high-throughput/scripts/channel-setup.sh", "w")
    fHandle.write('''
#
# Copyright IBM Corp All Rights Reserved
#
# SPDX-License-Identifier: Apache-2.0
#

ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Channel creation
echo "========== Creating channel: "$CHANNEL_NAME" =========="
peer channel create -o orderer.example.com:7050 -c $CHANNEL_NAME -f ../channel-artifacts/channel.tx --tls $CORE_PEER_TLS_ENABLED --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

declare -a peersCount=({peersCount})
for (( org=1; org<${{#peersCount[@]}}; ++org ))
do
    for (( peer=0; peer<${{peersCount[$org]}}; ++peer ))
    do
        echo "========== Joining peer$peer.org$org.example.com to channel mychannel =========="
        export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org$org.example.com/users/Admin@org$org.example.com/msp
        export CORE_PEER_ADDRESS=peer$peer.org$org.example.com:7051
        export CORE_PEER_LOCALMSPID="Org"$org"MSP"
        export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org$org.example.com/peers/peer$peer.org$org.example.com/tls/ca.crt
        peer channel join -b ${{CHANNEL_NAME}}.block
        if [ $peer -eq 0 ]
        then
             peer channel update -o orderer.example.com:7050 -c $CHANNEL_NAME -f ../channel-artifacts/${{CORE_PEER_LOCALMSPID}}anchors.tx --tls $CORE_PEER_TLS_ENABLED --cafile $ORDERER_CA
        fi
    done
done
'''.format(peersCount=" ".join(map(str, [0]+peersCount))))
    fHandle.close()

    fHandle = open("../high-throughput/scripts/install-chaincode.sh", "w")
    fHandle.write('''
#
# Copyright IBM Corp All Rights Reserved
#
# SPDX-License-Identifier: Apache-2.0
#

declare -a peersCount=({peersCount})
for (( org=1; org<${{#peersCount[@]}}; ++org ))
do
    for (( peer=0; peer<${{peersCount[$org]}}; ++peer ))
    do
        echo "========== Installing chaincode on peer$peer.org$org =========="
        export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org$org.example.com/users/Admin@org$org.example.com/msp
        export CORE_PEER_ADDRESS=peer$peer.org$org.example.com:7051
        export CORE_PEER_LOCALMSPID="Org"$org"MSP"
        export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org$org.example.com/peers/peer$peer.org$org.example.com/tls/ca.crt
        peer chaincode install -n $CC_NAME -v $1 -p github.com/hyperledger/fabric/examples/chaincode/go
    done
done
'''.format(peersCount=" ".join(map(str, [0]+peersCount))))
    fHandle.close()

    fHandle = open("../high-throughput/scripts/instantiate-chaincode.sh", "w")
    fHandle.write('''
#
# Copyright IBM Corp All Rights Reserved
#
# SPDX-License-Identifier: Apache-2.0
#

echo "========== Instantiating chaincode v$1 =========="
peer chaincode instantiate -o orderer.example.com:7050 --tls $CORE_PEER_TLS_ENABLED --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem -C $CHANNEL_NAME -n $CC_NAME -c '{{"Args": []}}' -v $1 -P "OR ({policy})"
'''.format(policy=",".join(["'Org{}MSP.member'".format(e) for e in range(1,orgsCount+1)])))
    fHandle.close()

    fHandle = open("../high-throughput/scripts/many-updates.sh", "w")
    fHandle.write('''
#
# Copyright IBM Corp All Rights Reserved
#
# SPDX-License-Identifier: Apache-2.0
#

init=true
org=1
peer=0
declare -a peersCount=({peersCount})

for (( i = 0; i < 1000; ++i ))
do
        export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org$org.example.com/users/Admin@org$org.example.com/msp
        export CORE_PEER_ADDRESS=peer$peer.org$org.example.com:7051
        export CORE_PEER_LOCALMSPID="Org"$org"MSP"
        export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org$org.example.com/peers/peer$peer.org$org.example.com/tls/ca.crt
        if [ "$init" = true ]
        then
                peer chaincode invoke -o orderer.example.com:7050  --tls $CORE_PEER_TLS_ENABLED --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem  -C $CHANNEL_NAME -n $CC_NAME -c '{{"Args":["update","'$1'","'$2'","'$3'"]}}'
        else
                peer chaincode invoke -o orderer.example.com:7050  --tls $CORE_PEER_TLS_ENABLED --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem  -C $CHANNEL_NAME -n $CC_NAME -c '{{"Args":["update","'$1'","'$2'","'$3'"]}}' &
        fi
        peer=$(expr $peer + 1)
        if [ $peer -eq ${{peersCount[$org]}} ]
        then
                org=$(expr $org + 1)
                peer=0
        fi
        if [ $org -eq ${{#peersCount[@]}} ]
        then
                org=1
                init=false
        fi
done
'''.format(peersCount=" ".join(map(str, [0]+peersCount))))
    fHandle.close()

def generate():
    kafka=True

    domainName = "example.com"
    orgsCount = 2
    orderersCount = 1
    zooKeepersCount = 3 if kafka else 0
    kafkasCount = 4 if kafka else 0
    peerCounts = [2, 2]

    genNetwork(domainName, orgsCount, orderersCount)
    genCrypto(domainName, orgsCount, orderersCount, peerCounts)
    p = subprocess.Popen(["./byfn.sh generate"], stdin=subprocess.PIPE, cwd=os.getcwd(), shell=True)
    p.communicate(input=b"y")
    p.wait()

    generateHighThroughput(domainName, orgsCount, peerCounts)
    generateDocker("hyperledger", "hyperledger-ov", domainName, orgsCount, orderersCount, peerCounts, zooKeepersCount, kafkasCount, "INFO")

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
