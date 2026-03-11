<?php
// SQL Server connection settings for the SixBit database.
// Uses Windows Authentication (no username/password required).
// Override via environment variables (SIXBIT_SERVER, SIXBIT_DB) if needed.
if (!defined('SIXBIT_SERVER')) {
	define('SIXBIT_SERVER', getenv('SIXBIT_SERVER') ?: 'SERVERWIN\\SIXBITDBSERVER');
}
if (!defined('SIXBIT_DB')) {
	define('SIXBIT_DB', getenv('SIXBIT_DB') ?: 'SixBit_BT_002');
}
