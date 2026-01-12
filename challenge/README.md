# Set-Up Instructions

We provide you two Docker containers, combined via docker-compose. While you can decide on your own what kind of
environment you want to use for development, please make sure that the final result will work in the provided
containers. It is accepted to change the Dockerfiles and/or docker-compose file if necessary for your solution.

Docker and docker-compose needs to be installed on your machine. To build and run the container network as a whole you
can use docker-compose directly:

    docker-compose up --build

If you want to build the containers separately, you can use `docker build` to do so:

    docker build -f Dockerfile-testrunner -t sony-nre-testwork-testrunner .
    docker build -f Dockerfile-service -t sony-nre-testwork-testservice .

The `service` container, described in `Dockerfile-service` is where we want you to implement your service for.

The `testrunner` container is the counterpart, supposed to test your solution. You are allowed to change this container
(and it's content), but it is not required or mandatory to do so.

# Task Overview

We are deploying a REST based network service, which is helping our organization to perform routing table lookups.

The tests provided within the `testrunner`-container should be able to run successful against the service build by you
within this task.

The service is fed by a full internet routing table (today, this consists of roughly one million routes). We are
providing you a "real" routing table along with this assignment you must use as your database (see `routes.txt`).
The format of the file is simply

    <prefix>;<next hop>

The REST service we want to deploy should expose an endpoint at

    /destination/<destination>

For instance, the HTTP request

    GET /destination/192.168.0.1

should perform a routing lookup for `192.168.0.1` and return the result in the following format

    {"dst": "<destination prefix>", "nh": "<next hop address>"}

If no route is found, the service shall return a HTTP 404 error.

The routing table look-up is supposed to implement the actual algorithm used to perform routing-table look-ups as
common operating systems implement it today (refer to [RFC 1812](https://www.ietf.org/rfc/rfc1812.txt) in case you
need help understanding how routers perform a routing table look-up).

Moreover, the service should support policy-based routing decisions, thus a metric value should be considered
accordingly when looking for the best route.

If entries have both, matching destination prefix and same metric, the best route should be selected based on the
lowest next-hop IP address in integer representation as a tie-breaker.

The service should support update a route's metric by sending a `PUT` request in the following format

    /prefix/<prefix>/nh/<next-hop>/metric/<metric>/match/<classifier>
    /prefix/<prefix>/nh/<next-hop>/metric/<metric>/

The classifier can be either `exact` or `orlonger`. When omitted, `orlonger` should be considered the default.

- If the classifier is set to `exact` only exact prefix matches should get the metric applied to.
- If the classifier is set to `orlonger` all prefixes, including all subnet-of prefixes would get the metric applied.
- next-hop should be always considered when updating a route entry

The metric is an integer in the range [1, 32768].

As it is common in the router world, the metric with the lowest value is preferred over metrics with a higher value.
The metric must be taken into consideration for any subsequent `GET /destination` table look-up thereafter.

For instance, the following HTTP request

    PUT /prefix/10.0.0.0%2F16/nh/192.168.1.100/metric/100

would apply the metric `100` to all matching routes within `10.0.0.0/16` that have `192.168.1.100` as next-hop.

The request should return the HTTP status code 200 if at least one route was updated, or 404 if no routes were updated.

# Testing Your Assignment

We are shipping a test client container you can use to test your service against. It is supposed to give you some
assistance to help bringing your service up. The tests we are shipping to you are **non-conclusive**. We will
perform more tests, than those we've sent to you, with more corner cases that we did not include in our copy handed
over to you.

## Running the Tests

The tests are implemented using `py.test`. It is recommended to simply run them by starting the docker compose-network.

If you want to start the tests manually, either just start the `testrunnner`-container or execute pytest locally from
your working directory. You might have to adjust the hostname used within the tests if you want to use the testrunner
locally.

# Submitting Your Assignment

Please submit your assignment as a self-sufficient compressed archive back to us. You may edit the `Dockerfile(s)`
as needed, to include everything allowing your service to run. You may add dependencies, scripts and whatever else you
need. The service you're submitting must not rely on an available internet connection at runtime.

# What We Will Be Looking At

You are generally free to implement the service in any way, we don't put restrictions on frameworks, libraries or
dependencies on you (but please submit Python 3 code). We will run and validate your code as you submit it. Roughly,
we will:

- look if you solved the problem in a correct way
- look what your approach to the problem was, and what the algorithmic complexity of it is
- how the quality of the code is you submit to us
- what the patterns and practices are you use

Try to keep the code quality on a level that you feel confident about, that you are familiar with and that you would
expect to see in production code.

We think, you should be able to clock-in somewhere around 8 hours to solve this problem. Take the time you need,
we don't value speed over quality. However, we might ask you for an estimate of how long it took you to write your
solution and which parts took you the longest and why you think that was the case.

You are allowed to change requirements, tests or anything else about this testtask. If you do so, please write down
the reasoning behind your change. In general, no writeup describing your solution or the process of solving this task
is required. Still, if you make interesting decisions or have anything else you want us to know/consider when
evaluating your solution, feel free to write as much as you like. We certainly enjoy getting an insight of your
approach and mindset while solving this task.
