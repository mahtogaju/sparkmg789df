CREATE TABLE IF NOT EXISTS dbo.FactSalesOrdersGold
(
    SalesOrderKey BIGINT IDENTITY(1,1) NOT NULL,
    OrderId VARCHAR(50) NOT NULL,
    CustomerId VARCHAR(50) NOT NULL,
    ProductId VARCHAR(50) NOT NULL,
    OrderDate DATE NOT NULL,
    Quantity INT NOT NULL,
    UnitPrice DECIMAL(18,2) NOT NULL,
    NetAmount DECIMAL(18,2) NOT NULL,
    LastModifiedUtc DATETIME2 NOT NULL
)
WITH
(
    DISTRIBUTION = HASH (OrderId),
    CLUSTERED COLUMNSTORE INDEX
);
GO

CREATE OR ALTER PROCEDURE dbo.usp_LoadGoldSalesOrders
    @WatermarkStart DATETIME2,
    @WatermarkEnd DATETIME2
AS
BEGIN
    SET NOCOUNT ON;

    MERGE dbo.FactSalesOrdersGold AS tgt
    USING
    (
        SELECT
            OrderId,
            CustomerId,
            ProductId,
            OrderDate,
            Quantity,
            UnitPrice,
            CAST(Quantity * UnitPrice AS DECIMAL(18,2)) AS NetAmount
        FROM dbo.SilverSalesOrders
        WHERE UpdatedOnUtc >= @WatermarkStart
          AND UpdatedOnUtc < @WatermarkEnd
    ) AS src
    ON tgt.OrderId = src.OrderId AND tgt.ProductId = src.ProductId
    WHEN MATCHED THEN
      UPDATE SET
          CustomerId = src.CustomerId,
          OrderDate = src.OrderDate,
          Quantity = src.Quantity,
          UnitPrice = src.UnitPrice,
          NetAmount = src.NetAmount,
          LastModifiedUtc = GETUTCDATE()
    WHEN NOT MATCHED THEN
      INSERT (OrderId, CustomerId, ProductId, OrderDate, Quantity, UnitPrice, NetAmount, LastModifiedUtc)
      VALUES (src.OrderId, src.CustomerId, src.ProductId, src.OrderDate, src.Quantity, src.UnitPrice, src.NetAmount, GETUTCDATE());
END;
GO
