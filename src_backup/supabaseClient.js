import { createClient } from '@supabase/supabase-js'

// ⚠️ IMPORTANTE: Estas credenciales NO son válidas aún
// Sigue estos pasos para obtener las credenciales reales:
// 
// 1. Ve a: https://supabase.com/dashboard/project/scpuriaofisssalsbzqv/settings/api
// 2. Copia el "Project URL" (debe ser exactamente: https://scpuriaofisssalsbzqv.supabase.co)
// 3. Copia la "anon/public key" - es un token JWT largo que empieza con "eyJ..."
// 4. Reemplaza los valores abajo con tus credenciales reales

const supabaseUrl = "https://scpuriaofisssalsbzqv.supabase.co"

// 🔑 REEMPLAZA ESTA LÍNEA CON TU CLAVE REAL:
// La clave real tiene ~300 caracteres y empieza con "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcHVyaWFvZmlzc3NhbHNienF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjgwNDksImV4cCI6MjA4NTkwNDA0OX0.oMYR_aV0SgMplBURwSESe8kLCWTl4QfQyOXsDfmBRfo"

// ⚠️ NO uses esta clave fake - no funcionará:
// const supabaseAnonKey = "sb_publishable_NfUDh2hQ_5HiFqnL7MNCeA_7MTs4_Kb"

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Verificación de conexión (opcional, para debugging)
// Descomentar para probar la conexión:
/*
supabase.from('productos').select('count', { count: 'exact', head: true })
  .then(({ count, error }) => {
    if (error) {
      console.error('❌ Error de conexión a Supabase:', error.message);
    } else {
      console.log('✅ Conexión exitosa a Supabase. Productos encontrados:', count);
    }
  });
*/
