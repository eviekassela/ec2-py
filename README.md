Requirements
------------

- [Python](http://www.python.org/download/) v.2.6 or later                                                               
  System's PYTHONPATH must be set to the latest installed version i.e. `/usr/bin/python2.6`
- [boto](https://github.com/boto/boto) (v.2.9.9 or later)
- [paramiko](https://github.com/paramiko/paramiko/) (v.1.11.0)
  - requires [pycrypto](https://github.com/dlitz/pycrypto) (v.2.6)

Use
---------
To use, simply untar, modify `Instance.properties` to your needs and run with:

```bash
python Execution.py start
```

This test version executes `run.sh` remotely, which modifies `testfile's` contents, and receives the changed file.
