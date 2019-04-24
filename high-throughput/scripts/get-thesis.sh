for (( i = 0; i < 100; ++i ))
do
	peer chaincode invoke -o orderer0.example.com:7050  --tls $CORE_PEER_TLS_ENABLED --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer0.example.com/msp/tlscacerts/tlsca.example.com-cert.pem  -C $CHANNEL_NAME -n $CC_NAME -c '{"Args":["get","'$i'"]}'
done
