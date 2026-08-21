-- Limpieza AhorraMas generada por revisar_matches_ahorramas.py
-- Fecha: 20260726_1412  |  Umbral: score < 5  |  Matches a anular: 28
-- Revisa matches_ahorramas_incorrectos_20260726_1412.csv antes de ejecutar.
-- Esto NO borra productos ni precios: solo rompe el vinculo catalogo<->AhorraMas
-- de los matches que la IA marco como malos.

UPDATE productos_match SET id_ahorramas = NULL
WHERE id_catalogo IN (
  'CAT-0544',
  'CAT-1003',
  'CAT-1005',
  'CAT-1007',
  'CAT-1015',
  'CAT-1016',
  'CAT-1782',
  'CAT-2003',
  'CAT-2074',
  'CAT-2369',
  'CAT-2532',
  'CAT-2557',
  'CAT-3003',
  'CAT-3975',
  'CAT-4568',
  'CAT-4684',
  'CAT-4686',
  'CAT-4687',
  'CAT-4748',
  'CAT-6250',
  'CAT-6410',
  'CAT-6662',
  'CAT-6769',
  'CAT-7277',
  'CAT-7870',
  'CAT-9233',
  'CAT-9745',
  'CAT-9778'
);
