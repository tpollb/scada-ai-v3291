import { writable } from 'svelte/store'

export interface LicenseStatus {
  valid: boolean
  expired: boolean
  in_grace_period: boolean
  days_remaining: number
  license_type: string
  features: string[]
  customer: string
  max_concurrent_users: number
  current_users: number
}

export const licenseStatus = writable<LicenseStatus | null>(null)
export const licenseError = writable<string | null>(null)

export async function fetchLicenseStatus() {
  try {
    const response = await fetch('http://localhost:8081/api/v1/license/status')
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const status: LicenseStatus = await response.json()
    licenseStatus.set(status)
    licenseError.set(null)
    return status
  } catch (e: any) {
    licenseError.set(e?.message || 'Failed to fetch license status')
    return null
  }
}
