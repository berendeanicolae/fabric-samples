package main

import (
    "github.com/hyperledger/fabric/core/chaincode/shim"
    sc "github.com/hyperledger/fabric/protos/peer"
    "strconv"
    "fmt"
)

type SmartContract struct {
}

func (s *SmartContract) Init(APIstub shim.ChaincodeStubInterface) sc.Response {
    return shim.Success(nil)
}

func (s *SmartContract) Invoke(APIstub shim.ChaincodeStubInterface) sc.Response {
    // Retrieve the requested Smart Contract function and arguments
    function, args := APIstub.GetFunctionAndParameters()
    // Route to the appropriate handler function to interact with the ledger appropriately
    if function == "initLedger" {
        return s.initLedger(APIstub, args)
    } else if function == "increment" {
        return s.increment(APIstub, args)
    }

    return shim.Error("Invalid Smart Contract function name.")
}


func (s *SmartContract) initLedger(APIstub shim.ChaincodeStubInterface, args []string) sc.Response {
    i := 0
    count, err := strconv.Atoi(args[0])
    if err != nil {
        return shim.Error(fmt.Sprintf("Could not convert %s to int", args[0]))
    }

    for i < count {
        bytes := []byte{0x00};
        APIstub.PutState("val_" + strconv.Itoa(i), bytes)
        i += 1
    }

    return shim.Success(nil)
}

func (s *SmartContract) increment(APIstub shim.ChaincodeStubInterface, args []string) sc.Response {
    value, err := APIstub.GetState("val_" + args[0])
    if err != nil {
        return shim.Error(fmt.Sprintf("Could not retrieve value #%s", args[0]))
    }

    value[0] += 1
    APIstub.PutState("val_" + args[0], value)

    return shim.Success(nil)
}

// The main function is only relevant in unit test mode. Only included here for completeness.
func main() {

	// Create a new Smart Contract
	err := shim.Start(new(SmartContract))
	if err != nil {
		fmt.Printf("Error creating new Smart Contract: %s", err)
	}
}
