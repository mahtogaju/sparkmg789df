CREATE TABLE IF NOT EXISTS dbo.SilverSalesOrders
(
    OrderId VARCHAR(50) NOT NULL,
    CustomerId VARCHAR(50) NOT NULL,
    OrderDate DATE NOT NULL,
    ProductId VARCHAR(50) NOT NULL,
    Quantity INT NOT NULL,
    UnitPrice DECIMAL(18,2) NOT NULL,
    NetAmount AS (Quantity * UnitPrice),
    RecordHash BINARY(32),
    UpdatedOnUtc DATETIME2 NOT NULL
);
GO

CREATE OR ALTER PROCEDURE dbo.usp_LoadSilverSalesOrders
AS
BEGIN
    SET NOCOUNT ON;

    WITH deduped AS
    (
        SELECT
            OrderId,
            CustomerId,
            CAST(OrderDate AS DATE) AS OrderDate,
            ProductId,
            Quantity,
            UnitPrice,
            HASHBYTES('SHA2_256', CONCAT(OrderId, '|', CustomerId, '|', ProductId, '|', Quantity, '|', UnitPrice)) AS RecordHash,
            ROW_NUMBER() OVER (PARTITION BY OrderId, ProductId ORDER BY IngestedOnUtc DESC) AS rn
        FROM dbo.BronzeSalesOrdersRaw
        WHERE OrderId IS NOT NULL
          AND CustomerId IS NOT NULL
          AND Quantity > 0
          AND UnitPrice >= 0
    )
    MERGE dbo.SilverSalesOrders AS tgt
    USING (SELECT * FROM deduped WHERE rn = 1) AS src
    ON tgt.OrderId = src.OrderId AND tgt.ProductId = src.ProductId
    WHEN MATCHED AND tgt.RecordHash <> src.RecordHash
      THEN UPDATE SET
            CustomerId = src.CustomerId,
            OrderDate = src.OrderDate,
            Quantity = src.Quantity,
            UnitPrice = src.UnitPrice,
            RecordHash = src.RecordHash,
            UpdatedOnUtc = GETUTCDATE()
    WHEN NOT MATCHED THEN
      INSERT (OrderId, CustomerId, OrderDate, ProductId, Quantity, UnitPrice, RecordHash, UpdatedOnUtc)
      VALUES (src.OrderId, src.CustomerId, src.OrderDate, src.ProductId, src.Quantity, src.UnitPrice, src.RecordHash, GETUTCDATE());
END;
GO
