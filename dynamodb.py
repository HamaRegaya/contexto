# Create users table if it doesn't exist
def create_users_table():
    try:
        table = dynamodb.create_table(
            TableName='ContextoUsers',
            KeySchema=[
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.wait_until_exists()
        print("Users table created successfully")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Users table already exists")
        else:
            print(f"Error creating table: {e}")
            raise

# Create game history table if it doesn't exist
def create_game_history_table():
    try:
        table = dynamodb.create_table(
            TableName='ContextoGameHistory',
            KeySchema=[
                {
                    'AttributeName': 'game_id',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'game_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'played_at',
                    'AttributeType': 'N'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIdIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'played_at',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.wait_until_exists()
        print("Game history table created successfully")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Game history table already exists")
            return True
        else:
            print(f"Error creating game history table: {e}")
            return False

# Create tables on startup
try:
    create_game_history_table()
except Exception as e:
    print(f"Error during table creation: {e}")