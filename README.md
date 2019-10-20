Django Multi-transaction test case
==================================

This is a work in progress. Much of the logic here is not Django-specific and could be refactored and extended to cover other cases where you want to test the interaction of more than one "transaction", whether that's a database transaction, processes competing for locks, etc.

The best documentation right now is [the included tests](./tests/). 

Contributions welcome.
