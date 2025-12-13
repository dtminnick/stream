
-- Create value stream hierarchy for Retirement Operations.

INSERT INTO stream (stream_id, level, stream_name, parent_stream_id)
VALUES (1, 0, 'Full-Service Retirement', NULL),
       (2, 1, 'Full-Service Retirement Operations', 1),
       (3, 2, 'Transition Services', 2),
       (4, 3, 'Client Services', 3),
	   (5, 3, 'Operations', 3),
	   (6, 3, 'Recordkeeping Help Desk', 3),
	   (7, 2, 'Retirement Operations', 2),
	   (8, 3, 'Money In', 7),
	   (9, 3, 'Money Out', 7),
	   (10, 3, 'Specialized Plan Services', 7),
	   (11, 3, 'ISG Call Support', 7),
	   (12, 3, '3(16) Support', 7),
	   (13, 2, 'Trade Investment Treasury', 2),
	   (14, 3, 'Trade', 13),
	   (15, 3, 'Treasury', 13),
	   (16, 3, 'Broker-Dealer Services', 13),
	   (17, 3, 'Fulfillment and Mail Operations', 13),
	   (18, 3, 'Accounting and Reconciliation', 13),
	   (19, 3, 'IT Production Support', 13),
	   (20, 2, 'Trust Services', 2),
	   (21, 3, 'Custodial Services', 20),
	   (22, 3, 'Cashiering', 20),
	   (23, 3, 'Tax Reporting', 20),
	   (24, 3, 'Cash Reconciliation', 20),
	   (25, 3, 'IRA Servicing', 20),
	   (26, 2, 'Document Services', 2),
	   (27, 3, 'Document Drafting', 26),
	   (28, 3, 'System Updates', 26),
	   (29, 3, 'Mass Regulatory Events', 26),
	   (30, 3, 'Specialty Document Services', 26),
	   (31, 2, 'Yearend Services', 2),
	   (32, 3, 'Non-Discrimination Testing', 31),
	   (33, 3, 'Plan Audit Support', 31),
	   (34, 3, 'Plan Reporting (Form 5500)', 31),
	   (35, 3, 'Employer Contribution Calculations', 31),
	   (36, 3, '3(16) Support', 31);

-- Map processes to level three streams.

INSERT INTO stream_process (stream_id, process_id)
VALUES (4, 101);