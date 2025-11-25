#!/usr/bin/env python3
"""
Script de prueba para el sistema de suscripciones
"""

from subscription_system import SubscriptionSystem
from auth_system import AuthSystem
import json

def test_subscription_system():
    print("🧪 Probando Sistema de Suscripciones...")
    
    # Inicializar sistemas
    auth_system = AuthSystem()
    subscription_system = SubscriptionSystem()
    
    print("\n1. 📋 Probando planes disponibles...")
    plans = subscription_system.get_all_plans()
    for plan in plans:
        print(f"   - {plan['display_name']}: ${plan['price']} - {plan['max_articles_per_day']} artículos/día")
    
    print("\n2. 👤 Probando suscripción de usuario...")
    # Crear un usuario de prueba
    test_user_id = 1  # Asumiendo que existe un usuario con ID 1
    
    # Obtener suscripción actual
    subscription = subscription_system.get_user_subscription(test_user_id)
    if subscription:
        print(f"   ✅ Usuario tiene suscripción activa: {subscription['plan_display_name']}")
    else:
        print("   ℹ️ Usuario sin suscripción activa (usará plan freemium)")
    
    print("\n3. 💳 Probando creación de código de pago...")
    premium_plan = next((p for p in plans if p['name'] == 'premium'), None)
    if premium_plan:
        payment_code = subscription_system.create_payment_code(test_user_id, premium_plan['id'])
        print(f"   ✅ Código de pago creado: {payment_code['code']}")
        print(f"   💰 Monto: ${payment_code['amount']}")
        print(f"   ⏰ Expira: {payment_code['expires_at']}")
        
        print("\n4. 🔍 Probando verificación de límites...")
        limits = subscription_system.check_usage_limits(test_user_id, 10, 5)
        print(f"   📊 Límites actuales:")
        print(f"      - Artículos: {limits['current_articles']}/{limits['max_articles']}")
        print(f"      - Imágenes: {limits['current_images']}/{limits['max_images']}")
        print(f"      - Plan: {limits['plan_name']}")
        print(f"      - Permitido: {'✅' if limits['allowed'] else '❌'}")
        
        print("\n5. ✅ Probando verificación de pago...")
        # Simular verificación de pago por admin
        admin_user_id = 1  # ID del admin
        success = subscription_system.verify_payment(payment_code['code'], admin_user_id, "Comprobante de prueba")
        if success:
            print("   ✅ Pago verificado exitosamente")
            
            # Verificar nueva suscripción
            new_subscription = subscription_system.get_user_subscription(test_user_id)
            if new_subscription:
                print(f"   🎉 Nueva suscripción activa: {new_subscription['plan_display_name']}")
        else:
            print("   ❌ Error verificando pago")
    
    print("\n6. 📈 Probando estadísticas...")
    pending_payments = subscription_system.get_pending_payments()
    print(f"   💳 Pagos pendientes: {len(pending_payments)}")
    
    user_payment_codes = subscription_system.get_user_payment_codes(test_user_id)
    print(f"   📋 Códigos de pago del usuario: {len(user_payment_codes)}")
    
    print("\n7. 🔄 Probando actualización de uso...")
    subscription_system.update_usage(test_user_id, 5, 3)
    print("   ✅ Uso actualizado: +5 artículos, +3 imágenes")
    
    # Verificar límites después del uso
    new_limits = subscription_system.check_usage_limits(test_user_id, 0, 0)
    print(f"   📊 Nuevos límites:")
    print(f"      - Artículos: {new_limits['current_articles']}/{new_limits['max_articles']}")
    print(f"      - Imágenes: {new_limits['current_images']}/{new_limits['max_images']}")
    
    print("\n🎉 Pruebas completadas exitosamente!")

if __name__ == "__main__":
    test_subscription_system()


















