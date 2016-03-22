# Asynchronous Proxy
This is an asynchronous proxy written with **Python 2.7** and **Twisted 16.0**.

## Requirements

1. Range requests support as defined in
[RFC2616](https://www.ietf.org/rfc/rfc2616.txt), but also via `range` query
parameter.

2. Return 416 error in case where both header and query parameter are
specified, but with different value.

3. Expose proxy statistics at /stats endpoint (total bytes transferred, uptime).

4. Proxy should be delivered with appropriate `Dockerfile` and
`docker-compose.yml`.

5. Proxy should be configureable via environmental variables.

## Installation 

- We must install `Docker`, `Docker compose`, `Docker engine` and `curl`.
- We can set an **Environment variable** for the proxy port.

Exemple:
```bash
$ export PROXY_PORT= 8080
```
- We start by cloning the repository from Github
```bash
$ git clone https://github.com/CatMirae/castlabs.git
$ cd castlabs
```
## Running 
- After that, we build the image using Docker and run our proxy with Compose Docker.
```bash
$ docker build -t asyncproxy .
$ docker-compose up 
```
## Testing
For the tests, we chose to work with this [text file] (http://norvig.com/big.txt).

1. Raising error for wrong path
    ```bash
    $ curl http://localhost:8080
    {
        "error": {
            "message": "Not Found", 
            "code": 404, 
            "description": "Path / not found"
        }
    }
    ```

2. Checking if there is no transferred bytes, when we run our proxy for the first time

    ```bash
    $ curl http://localhost:8080/stats
    {
        "message": "Ok", 
        "code": 200, 
        "stats": {
            "uptime": "0:00:38.122130", 
            "transferred_bytes": 0
        }
     }  
    ```
3. Testing if the Range requests is supported as defined in RFC2616
    ```bash
    $ curl -x http://localhost:8080 --range 0-20  http://norvig.com/big.txt
    
    The Project Gutenberg
    ```
4. Testing if the transferred bytes changed to 21 after the last request


    ```bash
    $ curl http://localhost:8080/stats
    {
        "message": "Ok", 
        "code": 200, 
        "stats": {
            "uptime": "0:01:06.020124", 
            "transferred_bytes": 21
        }
    }
    ```
    
5. Raising error when the header and query range request value are both present but not equal
    ```bash
    $ curl -x http://localhost:8080 --range 0-20  http://norvig.com/big.txt?range=8-11
    {
        "error": {
            "message": "Range Not Satisfiable", 
            "code": 416, 
            "description": "Range specified in header and query but with different values"
        }
    }
    ```
    
6. Checking if the transferred bytes does not change 
    ```bash
    $ curl http://localhost:8080/stats
    {
        "message": "Ok", 
        "code": 200, 
        "stats": {
            "uptime": "0:02:26.142487", 
            "transferred_bytes": 21
        }
    }
     ```
     
7. Sending request with range parameter 
    ```bash
    $ curl -x http://localhost:8080  http://norvig.com/big.txt?range=0-100
    
    The Project Gutenberg EBook of The Adventures of Sherlock Holmes
    by Sir Arthur Conan Doyle
    (#15 in ou
     ```
     
8. Checking if the transferred bytes changed to 122 
    ```bash
    $ curl http://localhost:8080/stats
    {
        "message": "Ok", 
        "code": 200, 
        "stats": {
            "uptime": "0:04:05.379367", 
            "transferred_bytes": 122
        }
    }
    ```

