
#
# Copyright IBM Corp All Rights Reserved
#
# SPDX-License-Identifier: Apache-2.0
#

org=1
peer=0
declare -a peersCount=(0 100)

for (( i = 0; i < 1000; ++i ))
do
        export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org$org.example.com/users/Admin@org$org.example.com/msp
        export CORE_PEER_ADDRESS=peer$peer.org$org.example.com:7051
        export CORE_PEER_LOCALMSPID="Org"$org"MSP"
        export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org$org.example.com/peers/peer$peer.org$org.example.com/tls/ca.crt
        peer chaincode invoke -o orderer0.example.com:7050  --tls $CORE_PEER_TLS_ENABLED --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer0.example.com/msp/tlscacerts/tlsca.example.com-cert.pem  -C $CHANNEL_NAME -n $CC_NAME -c '{"Args":["initPeer"]}' &
        peer=$(expr $peer + 1)
        if [ $peer -eq ${peersCount[$org]} ]
        then
                org=$(expr $org + 1)
                peer=0
        fi
        if [ $org -eq ${#peersCount[@]} ]
        then
                org=1
                break
        fi
done
