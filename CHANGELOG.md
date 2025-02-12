## CHANGELOG: stdio-mgr stdin/stdout/stderr mock/wrap context manager

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

### [Unreleased]

...

### [1.0.1] - 2019-02-11

#### Changed

 * `TeeStdin` is now a `slots=False` attrs class, to avoid errors arising
   from some manner of change in the vicinity of attrs v18.1/v18.2.

### [1.0.0] - 2018-04-01

#### Features

 * `stdio_mgr` context manager with capability for mocking/wrapping all three
   of `stdin`/`stdout`/`stderr`
 * `stdin` mocking/wrapping is implemented with the custom `TeeStdin`, a
   subclass of `StringIO`, which tees all content read from itself into
   the mocked/wrapped `stdout`
 * `TeeStdin` is extended from `StringIO` by an `.append()` method,
   which adds content to the end of the stream without changing the
   current seek position.

