# alb-creator-lambda

The following attributes need to be passed while invoking the lambda function:

| Attribute         | Description | Type | Default | Required |
|:------------------|:---------------------|:--------| :------------| :------|
| AppName | Name with which Target groups are created | String | None | Yes |
| OwnerContact | Email of the team owning the application | String | None | Yes |
| IamRole | IAM Role ARN | String | None | Yes |
| SubnetIds | String of Subnet IDs | String | None | Yes |
| SecurityGroups | String of Security Groups | String | None | Yes |
| Scheme | Load balancer type | String | `internal`| No |
| HealthCheckEnabled | Enabling the health check | String | `True` | No |
| HealthCheckPath | Path for health check | String | `/` | No |
| TargetType | Target type for the target group | String | `lambda` | No |
| rule_path | Path for listener rule | String | None | Yes |
| AlbName | Name of the ALB | String | None | Yes | 
| CertificateArn | ARN of the Certificate listener is attached to | String | None | Yes | SslPolicy | SSL policy in use | String | None | Yes | 