
1. ~~Add Generators and Generator Manager. Manager allows:~~
    ~~- register generator~~
    ~~- generate data using given args and kwargs~~
    ~~- support caching and cache retrieving (e.g. return same value) if ID argument is passed~~
2. ~~Add Matcher Manager:~~
    ~~- register matchers~~
    ~~- create matcher object by given name and using given args~~
    ~~- cache matcher objects and return cached object if args match~~
3. Add Compiler class:
    - plugs in JsonContent and uses wrapper to compile values of the structure
    - parses linse of "!any" and "!gen " values retriving: name of generator/matcher, args, kwargs and id (for generator)
    - using GeneratorManager or MatcherManager - create actual value/matcher
    - set generated value to Json
4. Use Compile on ApiConfigurationRead
5. ~~Optimize update of IterableJsonWrapper~~
6. ~~Remove negative index support for JsonWrapper~~
7. Make JsonWrapper and FlatJsonWrapper use similar error classes?



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
