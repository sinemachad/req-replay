# req-replay

> A CLI tool to capture, store, and replay HTTP requests for debugging and regression testing.

---

## Installation

```bash
pip install req-replay
```

Or install from source:

```bash
git clone https://github.com/yourname/req-replay.git && cd req-replay && pip install .
```

---

## Usage

**Capture** an HTTP request and save it to a file:

```bash
req-replay capture --url https://api.example.com/users --method GET --output captured.json
```

**Replay** a previously captured request:

```bash
req-replay replay --input captured.json
```

**Replay against a different base URL** (useful for regression testing):

```bash
req-replay replay --input captured.json --base-url https://staging.example.com
```

**Run a batch of captured requests:**

```bash
req-replay batch --dir ./requests/ --report results.html
```

---

## Features

- Capture requests with headers, query params, and body
- Store requests as portable JSON files
- Replay against any target environment
- Diff responses to catch regressions
- Simple CLI interface with no external dependencies

---

## License

This project is licensed under the [MIT License](LICENSE).