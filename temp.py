schema = {
    "age":{
        "required":True,
        "oneof":{
            "whole_number": {
                "type": "integer",
                "min": 18,
                "max": 115
            },
            "missing_value": {
                "type": "string",
                'allowed': ['Not Provided', 'Restricted', 'Not Collected']
            }
        }
    },
    "is_patient": {
        "required": True,
        "oneof":{
            "boolean_indicator": {
                "type": "string",
                "allowed": ["Yes","No"]
            },
            "missing_value": {
                "type": "string",
                'allowed': ['Restricted', 'Not Collected']
            }
        }
    }

}