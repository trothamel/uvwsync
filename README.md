# uvwsync: Tool for synchronizing a UV Workspace to a server.

## Note

This is intended for personal and day-job use. It's probably best to look at src/uvwsync/__init__.py
and mine it for idea, rather than use this project directly.

## Usage

```
uvwsync <package> <destination>
```

This should be run inside a UV Workspace. Destination should either be a directory, or an
remote path of the form user@host:/path or host:/path.

This finds all the packages in the current workspace that package depends on, including
transitive dependences. Dev-dependences and transitive dev-dependecies are also included.

The package and its dependencies are copied to the destination. The pyproject.toml file from
the workspace is also copied there. ``uv sync`` is then used on the server to install the
package's dependencies. Finally, if an ``after_deploy.sh`` file exists in the package,
it is run.

## License

Copyright (c) 2025 Tom Rothamel <tom@rothamel.us>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
