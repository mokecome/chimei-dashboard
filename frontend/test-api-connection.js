// Simple test script to verify API connectivity
const axios = require('axios')

const API_BASE_URL = 'http://127.0.0.1:8100/api'

async function testAPIConnection() {
  console.log('🧪 Testing API Connection...')
  console.log(`📡 Backend URL: ${API_BASE_URL}`)
  
  try {
    // Test 1: Basic connection - try auth endpoint instead
    console.log('\n1️⃣ Testing basic connection with auth endpoint...')
    try {
      await axios.post(`${API_BASE_URL}/auth/login`, {}, { timeout: 5000 })
    } catch (error) {
      if (error.response && [400, 422, 401].includes(error.response.status)) {
        console.log('✅ Backend is responding (expected error for empty login)')
      } else {
        throw error
      }
    }
    
    // Test 2: Auth endpoint availability
    console.log('\n2️⃣ Testing auth endpoints...')
    try {
      await axios.post(`${API_BASE_URL}/auth/login`, {
        email: 'test@test.com',
        password: 'wrongpassword'
      }, { timeout: 5000 })
    } catch (error) {
      if (error.response && error.response.status === 401) {
        console.log('✅ Auth endpoint responding (expected 401 for invalid credentials)')
      } else {
        throw error
      }
    }
    
    // Test 3: Default admin login (if available)
    console.log('\n3️⃣ Testing default admin login...')
    try {
      const loginResponse = await axios.post(`${API_BASE_URL}/auth/login`, {
        email: 'admin@chimei.com',
        password: 'admin123'
      }, { timeout: 5000 })
      
      if (loginResponse.data.access_token) {
        console.log('✅ Default admin login successful')
        console.log(`🔑 Token received: ${loginResponse.data.access_token.substring(0, 20)}...`)
        
        // Test 4: Authenticated request
        console.log('\n4️⃣ Testing authenticated request...')
        const meResponse = await axios.get(`${API_BASE_URL}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${loginResponse.data.access_token}`
          },
          timeout: 5000
        })
        console.log('✅ Authenticated request successful')
        console.log(`👤 User: ${meResponse.data.name} (${meResponse.data.role})`)
      }
    } catch (error) {
      console.log('⚠️ Default admin login failed (this is normal if not set up)')
    }
    
    console.log('\n🎉 API connectivity test completed successfully!')
    
  } catch (error) {
    console.error('\n❌ API connectivity test failed:')
    if (error.code === 'ECONNREFUSED') {
      console.error('🔌 Connection refused - Backend server is not running')
      console.error('💡 Make sure to start the backend server: cd backend && python run_server.py')
    } else if (error.code === 'ENOTFOUND') {
      console.error('🌐 Host not found - Check the backend URL')
    } else if (error.code === 'ETIMEDOUT') {
      console.error('⏰ Connection timeout - Backend is not responding')
    } else {
      console.error('🚨 Error:', error.message)
    }
    
    console.log('\n🔧 Troubleshooting steps:')
    console.log('1. Start the backend server: cd backend && python run_server.py')
    console.log('2. Check if the backend is running on port 8100')
    console.log('3. Verify the database connection is working')
    console.log('4. Check if there are any firewall issues')
  }
}

// Run the test
testAPIConnection()