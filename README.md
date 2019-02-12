# Tesla Powerwall

Crystal API for Tesla Powerwall.

## Installation

1. Add the dependency to your `shard.yml`:

   ```yaml
   dependencies:
     tesla-powerwall:
       github: jrester/tesla-powerwall
   ```

2. Run `shards install`

## Usage

To retrive Aggregates site:

```crystal
require "tesla-powerwall"

Tesla::Powerwall::Client.get "https://<your-domain>", Tesla::Powerwall::Client::Page::Aggregates
```

Currently these pages are supported:
* Aggregates
* Grid status
* State of Energy
* Site master

and these actions can be executed:
* Logout
* Stop
* Start

## Contributing

1. Fork it (<https://github.com/jrester/tesla-powerwall/fork>)
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create a new Pull Request

## Contributors

- [Jrester](https://github.com/jrester) - creator and maintainer
