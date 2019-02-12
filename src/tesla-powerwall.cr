require "json"
require "http/client"

module Tesla::Powerwall
  extend self

  class Object
    JSON.mapping(
      last_communication_time: String,
      instant_power: Float64,
      instant_reactive_power: Float64,
      instant_apparent_power: Float64,
      frequency: Float64,
      energy_exported: Float64,
      energy_imported: Float64,
      instant_average_voltage: Float64,
      instant_total_current: Float64,
      i_a_current: Int64,
      i_b_current: Int64,
      i_c_current: Int64,
      timeout: Int64?
    )
  end

  class Aggregates
    JSON.mapping(
      site: Object,
      battery: Object,
      load: Object,
      solar: Object,
      busway: Object,
      frequency: Object,
      generator: Object
    )
  end

  class GridStatus
    enum Status
      Connected,
      Down,
      Transition

      def from_json(parser : JSON::PullParser)
        case (status = parser.read_string)
        when "SystemGridConnected"
          Connected
        when "SystemIslandedActive"
          Down
        when "SystemTransitionToGrid"
          Transition
        else
          raise "Unknown grid status: #{status}!"
        end
      end

      def to_json(value : Status, builder : JSON::Builder)
        status = case value
        when Connected
          "SystemGridConnected"
        when Down
          "SystemIslandedActive"
        when Transition
          "SystemTransitionToGrid"
        else
          raise "Unkown grid status: #{value}"
        end
        status.to_json(builder)
      end
    end

    JSON.mapping(
      grid_status: Status,
      grid_services_active: Bool
    )
  end

  class StateOfEnergy
    JSON.mapping(
      percentage: Float64
    )
  end

  class SiteMaster
    JSON.mapping(
      running: Bool,
      uptime: String|Time,
      connected_to_tesla: Bool
    )
  end

  class Client
    enum Action
      Logout,
      Start,
      Stop

      def encode
        case self
        when Logout
          "/api/logout"
        when Start
          "/api/sitemaster/run"
        when Stop
          "/api/sitemaster/stop"
        else
          raise "Unkown action: #{self}!"
        end
      end
    end

    enum Page
      Aggregates,
      GridStatus,
      StateOfEnergy,
      SiteMaster,

      def encode : String
        case self
        when Aggregates
           "/api/meters/aggregates"
        when GridStatus
          "/api/system_status/grid_status"
        when StateOfEnergy
          "/api/system_status/soe"
        when SiteMaster
          "/api/sitemaster "
        else
          raise "Unknown page: #{self}!"
        end
      end

      def object_for_page
        case self
        when Aggregates
           Tesla::Powerwall::Aggregates
        when GridStatus
          Tesla::Powerwall::GridStatus
        when StateOfEnergy
          Tesla::Powerwall::StateOfEnergy
        when SiteMaster
          Tesla::Powerwall::SiteMaster
        else
          raise "Unknown page: #{self}!"
        end
      end
    end

    def initialize(endpoint : String)
      @client = HTTP::Client.new endpoint
    end

    def self.get(endpoint : String, page : Page)
      client = Client.new endpoint
      client.get page
    end

    def get(page : Page)
      response = @client.get page.encode
      page.object_for_page.from_json response.body
    end

    def self.execute(endpoint : String, action : Action)
      client = Client.new endpoint
      client.get page
    end

    def execute(action : Action)
      response = @client.get action.encode
    end
  end
end
