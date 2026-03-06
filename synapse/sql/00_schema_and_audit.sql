CREATE TABLE IF NOT EXISTS dbo.IngestionAudit
(
    AuditId BIGINT IDENTITY(1,1),
    LayerName VARCHAR(20) NOT NULL,
    SourceFile VARCHAR(260) NOT NULL,
    PipelineRunId VARCHAR(64) NOT NULL,
    IngestedOnUtc DATETIME2 NOT NULL,
    Status VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS dbo.BronzeSalesOrdersRaw
(
    OrderId VARCHAR(50),
    CustomerId VARCHAR(50),
    OrderDate DATETIME2,
    ProductId VARCHAR(50),
    Quantity INT,
    UnitPrice DECIMAL(18,2),
    SourceFileName VARCHAR(260),
    IngestedOnUtc DATETIME2
);
