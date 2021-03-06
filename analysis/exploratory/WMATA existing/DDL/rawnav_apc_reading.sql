--------------------------------------------------------
--  File created - Tuesday-February-11-2020   
--------------------------------------------------------
--------------------------------------------------------
--  DDL for Table RAWNAV_APC_READING
--------------------------------------------------------

  CREATE TABLE "PLANAPI"."RAWNAV_APC_READING" 
   (	"ID" NUMBER, 
	"X1" NUMBER, 
	"X2" NUMBER, 
	"X3" NUMBER, 
	"X4" NUMBER, 
	"X5" NUMBER, 
	"X6" NUMBER, 
	"LAST_GPS_READING_ID" NUMBER
   ) SEGMENT CREATION IMMEDIATE 
  PCTFREE 10 PCTUSED 40 INITRANS 1 MAXTRANS 255 
 NOCOMPRESS LOGGING
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1
  BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)
  TABLESPACE "PLANAPI_T" ;
--------------------------------------------------------
--  DDL for Index RAWNAV_APC_READING_PK
--------------------------------------------------------

  CREATE UNIQUE INDEX "PLANAPI"."RAWNAV_APC_READING_PK" ON "PLANAPI"."RAWNAV_APC_READING" ("ID") 
  PCTFREE 10 INITRANS 2 MAXTRANS 255 COMPUTE STATISTICS 
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1
  BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)
  TABLESPACE "PLANAPI_T" ;
--------------------------------------------------------
--  Constraints for Table RAWNAV_APC_READING
--------------------------------------------------------

  ALTER TABLE "PLANAPI"."RAWNAV_APC_READING" ADD CONSTRAINT "RAWNAV_APC_READING_PK" PRIMARY KEY ("ID")
  USING INDEX PCTFREE 10 INITRANS 2 MAXTRANS 255 COMPUTE STATISTICS 
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1
  BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)
  TABLESPACE "PLANAPI_T"  ENABLE;
  ALTER TABLE "PLANAPI"."RAWNAV_APC_READING" MODIFY ("ID" NOT NULL ENABLE);
