

4. Add headers check to ApiResponseHelper
5.





### Instructions

`!ref $defines/stuff`          --- local file reference
`!file content.json`           --- load from file
`!import !ref $defines/stuff ` --- import as `!ref $defines/stuff`
`!import !file content.json`   --- import as `!file content.json`

### Use cases
```json
// requsts.json
{
    "$": {
        "foo": "bar",
        "schema": "!file schemas.json"
    },
    "MyReq": {
        "request": {
            "path": "!ref $/foo/bar"
        },
        "response": {
            "schema": "!ref $/schema/MySchema"
        }
    }
}

// headers.json
{
    "$": {
        "content_json": "application/json"
    }

    "header_ok": {
        "Content-Type": "!ref $/content_json",
        "Allow": "GET, HEAD"
    },
    "header_post": "!combine !ref $/header_ok | !add_node MyKey: MyValue | !add_nodes !ref $/header_ok"
    /*

    {
        "Content-Type": "!ref $/content_json",
        "Allow": "GET, HEAD",
        "MyKey": "MyValue",
        "Content-Type": "!ref $/content_json",
        "Allow": "GET, HEAD",
    },
    */

}


// schema.json
{
    "$": {
        "type_filename": {
            "type": "string",
            "format": "abcde"
        }
    }

    "MySchema1": {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "message": "!ref $/type_filename",
            "status": {
                "type": "string",
                "enum": ["success","error"]
            }
        }
    },
    "MySchema2": {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "message": "!ref $/type_filename",
            "status": {
                "type": "string",
                "enum": ["success","error"]
            }
        }
    },

}

```
