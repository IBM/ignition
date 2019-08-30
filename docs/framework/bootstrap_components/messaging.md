# Messaging

Messaging is a core feature required by many of the Services expected in a VIM or VNFC driver. As a result, all of the Services listed below are enabled by default when using the `ignition.boot.api.build_vim_driver` or `ignition.boot.api.build_vnfc_driver` method. 

In Ignition, messaging has been split down into 4 areas:

- Sending - the act of sending a message
- Posting - the act of "enveloping" a message making it ready for delivery
- Delivery - the act of getting the message to the target destination
- Inbox - receiving a message

The act of sending a message is often unique depending on who is sending one and why. However; posting and delivering messages are often common tasks that can be performed by a central system. Handling the receipt of a message is also often unique, although the task of providing an inbox for messages to go is not.

As a result there are 4 services that may be auto-configured:

| Name                 | Capability         | Required Capabilities | Bootstrap Enable/Disable flag        | Description                                                            |
| -------------------- | ------------------ | --------------------- | ------------------------------------ | ---------------------------------------------------------------------- |
| PostalService        | PostalCapability   | DeliveryCapability    | bootstrap.messaging.postal_enabled   | Handles sent messages and gets them to the configured delivery service |
| KafkaDeliveryService | DeliveryCapability | -                     | bootstrap.messaging.delivery_enabled | Handles delivering messages to the desired Kafka topic                 |
| KafkaInboxService    | InboxCapability    | -                     | bootstrap.messaging.inbox_enabled    | Handles watching desired Kafka topics for new messages                 |

With these services in place, different types of messaging sending services can be created that re-use the functionality of posting and delivering them (for example see the InfrastructureMessagingService).