#!/usr/bin/env python3

import os
import unittest
from hashlib import sha256

from btclib.numbertheory import legendre_symbol
from btclib.ellipticcurves import secp256k1, secp224k1, int_from_Scalar, \
                                  bytes_from_Point, to_Point, \
                                  pointMultiply
from btclib.ecssa import rfc6979, int_from_hash, \
                         ecssa_sign, ecssa_sign, to_ssasig, \
                         _ecssa_verify, ecssa_verify, \
                         _ecssa_pubkey_recovery, \
                         ecssa_batch_validation

from tests.test_ellipticcurves import low_card_curves

class TestEcssa(unittest.TestCase):

    def test_ecssa(self):
        """Basic tests"""
        q = 0x1
        Q = pointMultiply(secp256k1, q, secp256k1.G)
        msg = sha256('Satoshi Nakamoto'.encode()).digest()
        ssasig = ecssa_sign(msg, q)
        # no source for the following... but
        # https://bitcointalk.org/index.php?topic=285142.40
        # same r because of rfc6979
        exp_sig = (0x934B1EA10A4B3C1757E2B0C017D0B6143CE3C9A7E6A4A49860D7A6AB210EE3D8,
                   0x2DF2423F70563E3C4BD0E00BDEF658081613858F110ECF937A2ED9190BF4A01A)
        r, s = to_ssasig(ssasig, secp256k1)
        self.assertEqual(r, exp_sig[0])
        self.assertEqual(s, exp_sig[1])
        
        self.assertTrue(ecssa_verify(ssasig, msg, Q))
        self.assertTrue(_ecssa_verify(ssasig, msg, Q))

        fmsg = sha256('Craig Wright'.encode()).digest()
        self.assertFalse(ecssa_verify(ssasig, fmsg, Q))
        self.assertFalse(_ecssa_verify(ssasig, fmsg, Q))

        fssasig = (ssasig[0], ssasig[1], ssasig[1])
        self.assertFalse(ecssa_verify(fssasig, msg, Q))
        self.assertRaises(TypeError, _ecssa_verify, fssasig, msg, Q)

        # y(sG - eP) is not a quadratic residue
        fq = 0x2
        fQ = pointMultiply(secp256k1, fq, secp256k1.G)
        self.assertFalse(ecssa_verify(ssasig, msg, fQ))
        self.assertRaises(ValueError, _ecssa_verify, ssasig, msg, fQ)

        fq = 0x4
        fQ = pointMultiply(secp256k1, fq, secp256k1.G)
        self.assertFalse(ecssa_verify(ssasig, msg, fQ))
        self.assertFalse(_ecssa_verify(ssasig, msg, fQ))

        # not ec.pIsThreeModFour
        self.assertFalse(ecssa_verify(ssasig, msg, Q, secp224k1))
        self.assertRaises(ValueError, _ecssa_verify, ssasig, msg, Q, secp224k1)

    def test_schnorr_bip_tv(self):
        """Bip-Schnorr Test Vectors
       
        https://github.com/sipa/bips/blob/bip-schnorr/bip-schnorr.mediawiki
        """

        # test vector 1
        prv = b'\x00' * 31 + b'\x01'
        pub = pointMultiply(secp256k1, prv, secp256k1.G)
        msg = b'\x00' * 32
        expected_sig = (0x787A848E71043D280C50470E8E1532B2DD5D20EE912A45DBDD2BD1DFBF187EF6,
                        0x7031A98831859DC34DFFEEDDA86831842CCD0079E1F92AF177F7F22CC1DCED05)
        eph_prv = int.from_bytes(sha256(prv + msg).digest(), byteorder="big")
        sig = ecssa_sign(msg, prv, eph_prv)
        self.assertTrue(_ecssa_verify(sig, msg, pub))
        self.assertEqual(sig, expected_sig)
        e = sha256(sig[0].to_bytes(32, byteorder="big") +
                   bytes_from_Point(secp256k1, pub, True) +
                   msg).digest()
        self.assertEqual(_ecssa_pubkey_recovery(sig, e, secp256k1), pub)

        # test vector 2
        prv =              0xB7E151628AED2A6ABF7158809CF4F3C762E7160F38B4DA56A784D9045190CFEF
        pub = pointMultiply(secp256k1, prv, secp256k1.G)
        msg = bytes.fromhex("243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89")
        expected_sig =    (0x2A298DACAE57395A15D0795DDBFD1DCB564DA82B0F269BC70A74F8220429BA1D,
                           0x1E51A22CCEC35599B8F266912281F8365FFC2D035A230434A1A64DC59F7013FD)
        eph_prv = int.from_bytes(sha256(prv.to_bytes(32, byteorder="big") + msg).digest(), byteorder="big")
        sig = ecssa_sign(msg, prv, eph_prv)
        self.assertTrue(_ecssa_verify(sig, msg, pub))
        self.assertEqual(sig, expected_sig)
        e = sha256(sig[0].to_bytes(32, byteorder="big") +
                   bytes_from_Point(secp256k1, pub, True) +
                   msg).digest()
        self.assertEqual(_ecssa_pubkey_recovery(sig, e, secp256k1), pub)

        # test vector 3
        prv =              0xC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B14E5C7
        pub = pointMultiply(secp256k1, prv, secp256k1.G)
        msg = bytes.fromhex("5E2D58D8B3BCDF1ABADEC7829054F90DDA9805AAB56C77333024B9D0A508B75C")
        expected_sig =    (0x00DA9B08172A9B6F0466A2DEFD817F2D7AB437E0D253CB5395A963866B3574BE,
                           0x00880371D01766935B92D2AB4CD5C8A2A5837EC57FED7660773A05F0DE142380)
        eph_prv = int.from_bytes(sha256(prv.to_bytes(32, byteorder="big") + msg).digest(), byteorder="big")
        sig = ecssa_sign(msg, prv, eph_prv)
        self.assertTrue(_ecssa_verify(sig, msg, pub))
        self.assertEqual(sig, expected_sig)
        e = sha256(sig[0].to_bytes(32, byteorder="big") +
                   bytes_from_Point(secp256k1, pub, True) +
                   msg).digest()
        self.assertEqual(_ecssa_pubkey_recovery(sig, e, secp256k1), pub)

        # test vector 4
        pub = "03DEFDEA4CDB677750A420FEE807EACF21EB9898AE79B9768766E4FAA04A2D4A34"
        msg =   "4DF3C3F68FCC83B27E9D42C90431A72499F17875C81A599B566C9889B9696703"
        sig = (0x00000000000000000000003B78CE563F89A0ED9414F5AA28AD0D96D6795F9C63,
               0x02A8DC32E64E86A333F20EF56EAC9BA30B7246D6D25E22ADB8C6BE1AEB08D49D)
        self.assertTrue(_ecssa_verify(sig, msg, pub))
        e = sha256(sig[0].to_bytes(32, byteorder="big") +
                   bytes_from_Point(secp256k1, pub, True) +
                   bytes.fromhex(msg)).digest()
        self.assertEqual(_ecssa_pubkey_recovery(sig, e, secp256k1), to_Point(secp256k1, pub))

        # test vector 5
        # test would fail if jacobi symbol of x(R) instead of y(R) is used
        pub = "031B84C5567B126440995D3ED5AABA0565D71E1834604819FF9C17F5E9D5DD078F"
        msg =   "0000000000000000000000000000000000000000000000000000000000000000"
        sig = (0x52818579ACA59767E3291D91B76B637BEF062083284992F2D95F564CA6CB4E35,
               0x30B1DA849C8E8304ADC0CFE870660334B3CFC18E825EF1DB34CFAE3DFC5D8187)
        self.assertTrue(_ecssa_verify(sig, msg, pub))
        e = sha256(sig[0].to_bytes(32, byteorder="big") +
                   bytes_from_Point(secp256k1, pub, True) +
                   bytes.fromhex(msg)).digest()
        self.assertEqual(_ecssa_pubkey_recovery(sig, e, secp256k1), to_Point(secp256k1, pub))

        # test vector 6
        # test would fail if msg is reduced
        pub = "03FAC2114C2FBB091527EB7C64ECB11F8021CB45E8E7809D3C0938E4B8C0E5F84B"
        msg =   "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
        sig = (0x570DD4CA83D4E6317B8EE6BAE83467A1BF419D0767122DE409394414B05080DC,
               0xE9EE5F237CBD108EABAE1E37759AE47F8E4203DA3532EB28DB860F33D62D49BD)
        self.assertTrue(_ecssa_verify(sig, msg, pub))
        e = sha256(sig[0].to_bytes(32, byteorder="big") +
                   bytes_from_Point(secp256k1, pub, True) +
                   bytes.fromhex(msg)).digest()
        self.assertEqual(_ecssa_pubkey_recovery(sig, e, secp256k1), to_Point(secp256k1, pub))

        # new proposed test: test would fail if msg is reduced
        pub = "03FAC2114C2FBB091527EB7C64ECB11F8021CB45E8E7809D3C0938E4B8C0E5F84B"
        msg =   "000008D8B3BCDF1ABADEC7829054F90DDA9805AAB56C77333024B9D0A5000000"
        sig = (0x3598678C6C661F02557E2F5614440B53156997936FE54A90961CFCC092EF789D,
               0x41E4E4386E54C924251679ADD3D837367EECBFF248A3DE7C2DB4CE52A3D6192A)
        self.assertTrue(_ecssa_verify(sig, msg, pub))
        e = sha256(sig[0].to_bytes(32, byteorder="big") +
                   bytes_from_Point(secp256k1, pub, True) +
                   bytes.fromhex(msg)).digest()
        self.assertEqual(_ecssa_pubkey_recovery(sig, e, secp256k1), to_Point(secp256k1, pub))

        # new proposed test: genuine failure
        pub = "03FAC2114C2FBB091527EB7C64ECB11F8021CB45E8E7809D3C0938E4B8C0E5F84B"
        msg =   "0000000000000000000000000000000000000000000000000000000000000000"
        sig = (0x3598678C6C661F02557E2F5614440B53156997936FE54A90961CFCC092EF789D,
               0x41E4E4386E54C924251679ADD3D837367EECBFF248A3DE7C2DB4CE52A3D6192A)
        self.assertFalse(_ecssa_verify(sig, msg, pub))

        # test vector 7
        # public key not on the curve
        pub = "03EEFDEA4CDB677750A420FEE807EACF21EB9898AE79B9768766E4FAA04A2D4A34"
        msg =   "4DF3C3F68FCC83B27E9D42C90431A72499F17875C81A599B566C9889B9696703"
        sig = (0x00000000000000000000003B78CE563F89A0ED9414F5AA28AD0D96D6795F9C63,
               0x02A8DC32E64E86A333F20EF56EAC9BA30B7246D6D25E22ADB8C6BE1AEB08D49D)
        self.assertRaises(ValueError, _ecssa_verify, sig, msg, pub)

        # test vector 8
        # Incorrect sig: incorrect R residuosity
        pub = "02DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659"
        msg =   "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89"
        sig = (0x2A298DACAE57395A15D0795DDBFD1DCB564DA82B0F269BC70A74F8220429BA1D,
               0xFA16AEE06609280A19B67A24E1977E4697712B5FD2943914ECD5F730901B4AB7)
        self.assertRaises(ValueError, _ecssa_verify, sig, msg, pub)

        # test vector 9
        # Incorrect sig: negated message hash
        pub = "03FAC2114C2FBB091527EB7C64ECB11F8021CB45E8E7809D3C0938E4B8C0E5F84B"
        msg =   "5E2D58D8B3BCDF1ABADEC7829054F90DDA9805AAB56C77333024B9D0A508B75C"
        sig = (0x00DA9B08172A9B6F0466A2DEFD817F2D7AB437E0D253CB5395A963866B3574BE,
               0xD092F9D860F1776A1F7412AD8A1EB50DACCC222BC8C0E26B2056DF2F273EFDEC)
        self.assertRaises(ValueError, _ecssa_verify, sig, msg, pub)

        # test vector 10
        # Incorrect sig: negated s value
        pub = "0279BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798"
        msg = b'\x00' * 32
        sig = (0x787A848E71043D280C50470E8E1532B2DD5D20EE912A45DBDD2BD1DFBF187EF6,
               0x8FCE5677CE7A623CB20011225797CE7A8DE1DC6CCD4F754A47DA6C600E59543C)
        self.assertRaises(ValueError, _ecssa_verify, sig, msg, pub)

        # test vector 11
        # Incorrect sig: negated public key
        pub = bytes.fromhex("03DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659")
        msg =   bytes.fromhex("243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89")
        sig =               (0x2A298DACAE57395A15D0795DDBFD1DCB564DA82B0F269BC70A74F8220429BA1D,
                             0x1E51A22CCEC35599B8F266912281F8365FFC2D035A230434A1A64DC59F7013FD)
        self.assertRaises(ValueError, _ecssa_verify, sig, msg, pub)

        # test vector 12
        # sG - eP is infinite.
        # Test fails in single verification if jacobi(y(inf)) is defined as 1 and x(inf) as 0
        pub = bytes.fromhex("02DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659")
        msg =   bytes.fromhex("243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89")
        sig =               (0x0000000000000000000000000000000000000000000000000000000000000000,
                             0x9E9D01AF988B5CEDCE47221BFA9B222721F3FA408915444A4B489021DB55775F)
        self.assertRaises(ValueError, _ecssa_verify, sig, msg, pub)

        # test vector 13
        # sG - eP is infinite.
        # Test fails in single verification if jacobi(y(inf)) is defined as 1 and x(inf) as 1"""
        pub = to_Point(secp256k1, "02DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659")
        msg =  bytes.fromhex("243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89")
        sig =              (0x0000000000000000000000000000000000000000000000000000000000000001,
                            0xD37DDF0254351836D84B1BD6A795FD5D523048F298C4214D187FE4892947F728)
        self.assertRaises(ValueError, _ecssa_verify, sig, msg, pub)

        # test vector 14
        # sig[0:32] is not an X coordinate on the curve
        pub = to_Point(secp256k1, "02DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659")
        msg =  bytes.fromhex("243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89")
        sig =              (0x4A298DACAE57395A15D0795DDBFD1DCB564DA82B0F269BC70A74F8220429BA1D,
                            0x1E51A22CCEC35599B8F266912281F8365FFC2D035A230434A1A64DC59F7013FD)
        self.assertRaises(ValueError, _ecssa_verify, sig, msg, pub)

        # test vector 15
        # sig[0:32] is equal to field size
        pub = to_Point(secp256k1, "02DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659")
        msg =  bytes.fromhex("243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89")
        sig =              (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC2F,
                            0x1E51A22CCEC35599B8F266912281F8365FFC2D035A230434A1A64DC59F7013FD)
        self.assertRaises(ValueError, _ecssa_verify, sig, msg, pub)

        # test vector 16
        # sig[32:64] is equal to curve order
        pub = to_Point(secp256k1, "02DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659")
        msg =  bytes.fromhex("243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89")
        sig =              (0x2A298DACAE57395A15D0795DDBFD1DCB564DA82B0F269BC70A74F8220429BA1D,
                            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141)
        self.assertRaises(ValueError, _ecssa_verify, sig, msg, pub)

    def test_low_cardinality(self):
        """test all msg/key pairs of low cardinality elliptic curves"""

        # ec.n has to be prime to sign
        prime = [
              3,   5,   7,  11,  13,  17,  19,  23,  29,  31,
             37,  41,  43,  47,  53,  59,  61,  67,  71,  73#,
            # 79,  83,  89,  97, 101, 103, 107, 109, 113, 127,
            #131, 137, 139, 149, 151, 157, 163, 167, 173, 179,
            #181, 191, 193, 197, 199, 211, 223, 227, 229, 233,
            #239, 241, 251, 257, 263, 269, 271, 277, 281, 283
            ]

        # all possible hashed messages
        hlen = 32
        H = [i.to_bytes(hlen, 'big') for i in range(0, max(prime))]

        for ec in low_card_curves: # only low card curves or it would take forever
            if ec.n in prime: # only few curves or it would take too long
                # Schnorr-bip only applies to curve whose prime p = 3 %4
                if not ec.pIsThreeModFour:
                    self.assertRaises(ValueError, ecssa_sign, H[0], 1, None, ec)
                    continue
                # all possible private keys (invalid 0 included)
                for q in range(0, ec.n):
                    if q == 0:
                        self.assertRaises(ValueError, ecssa_sign, H[0], q, None, ec)
                        continue
                    Q = pointMultiply(ec, q, ec.G) # public key
                    for m in range(0, ec.n): # all possible hashed messages

                        k = rfc6979(q, H[m], ec, sha256) # ephemeral key
                        K = pointMultiply(ec, k, ec.G)
                        if K[1] == 0:
                            self.assertRaises(ValueError, ecssa_sign, H[m], q, k, ec)
                            continue
                        if legendre_symbol(K[1], ec._p) != 1:
                            k = ec.n - k

                        ebytes  = K[0].to_bytes(ec.bytesize, byteorder="big")
                        ebytes += bytes_from_Point(ec, Q, True)
                        ebytes += H[m]
                        ebytes = sha256(ebytes).digest()
                        e = int_from_hash(ebytes, ec, sha256)
                        s = (k + e * q) % ec.n

                        # valid signature
                        sig = ecssa_sign(H[m], q, k, ec)
                        self.assertEqual((K[0], s), sig)
                        # valid signature must validate
                        self.assertTrue(_ecssa_verify(sig, H[m], Q, ec))

    def test_batch_validation(self):
        m = []
        sig = []
        Q = []
        a = []
        for i in range(0, 50):
            m.append(os.urandom(secp256k1.bytesize))
            q = int_from_Scalar(secp256k1, os.urandom(secp256k1.bytesize))
            sig.append(ecssa_sign(m[i], q))
            Q.append(pointMultiply(secp256k1, q, secp256k1.G))
            a.append(int.from_bytes(os.urandom(secp256k1.bytesize), 'big')) #FIXME:%?
        self.assertTrue(ecssa_batch_validation(sig, m, Q, a, secp256k1))

        m.append(m[0])
        sig.append(sig[1]) # invalid
        Q.append(Q[0])
        a.append(a[0])
        self.assertFalse(ecssa_batch_validation(sig, m, Q, a, secp256k1))

if __name__ == "__main__":
    # execute only if run as a script
    unittest.main()
