# AWS Event-Driven Order Processing System

## Overview

This project is a hands-on AWS serverless build that demonstrates event-driven order processing, asynchronous workflows, retry/failure handling, and basic operational visibility.

The system will accept order submissions through an API, store order state, process orders in the background, and document both successful and failure paths.

## Scenario

A small ordering system receives customer orders through an API. Orders are validated, stored, processed asynchronously, and monitored through logs and alarms.

## Planned Architecture

Initial MVP flow:

1. API Gateway receives an order request.
2. Ingestion Lambda validates the payload.
3. Valid orders are written to DynamoDB.
4. DynamoDB Streams trigger a processing Lambda.
5. Processing Lambda updates order status.
6. Failure handling, retry queues, DLQ, alerts, and high-value routing are added in later phases.

## Services Planned

- Amazon API Gateway
- AWS Lambda
- Amazon DynamoDB
- DynamoDB Streams
- Amazon SQS
- Amazon SNS
- Amazon CloudWatch
- IAM
- Terraform

## Cost Control

This project is designed to use low-cost, serverless, pay-per-use AWS services where practical.

Resources should be destroyed after testing unless there is a deliberate reason to keep them.

## Repository Structure

```text
docs/         Project documentation
examples/     Example request payloads
infra/        Terraform infrastructure
postman/      Postman collection and environment exports
src/          Lambda source code
screenshots/  Portfolio evidence screenshots
Status

Project scaffold created. AWS resources have not been deployed yet.
