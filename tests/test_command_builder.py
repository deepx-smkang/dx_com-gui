#!/usr/bin/env python3
"""
Unit test for command builder logic in Task 4.2.

Tests that the _build_command() method correctly translates
GUI configuration into dxcom command-line arguments.
"""
import sys
import os

# Add parent directory to path to import src package
sys.path.insert(0, os.path.dirname(__file__))

from src.dxcom_wrapper import DXComExecutor


def test_minimal_configuration():
    """Test command building with minimal configuration."""
    print("Test 1: Minimal Configuration")
    print("-" * 60)
    
    options = {
        'config_path': '',
        'opt_level': 0,
        'gen_log': False,
        'aggressive_partitioning': False,
        'compile_input_nodes': '',
        'compile_output_nodes': ''
    }
    
    executor = DXComExecutor(
        input_path='/models/model.onnx',
        output_path='/output/model.dxnn',
        compiler_options=options
    )
    
    cmd = executor._build_command()
    print(f"Generated command: {' '.join(cmd)}")
    
    # Verify
    assert cmd[0] == 'dxcom', "First arg should be 'dxcom'"
    assert cmd[1] == '-m', "Second arg should be '-m' flag"
    assert cmd[2] == '/models/model.onnx', "Third arg should be input path"
    assert cmd[3] == '-o', "Fourth arg should be '-o' flag"
    assert '/output' in cmd[4], "Fifth arg should be output directory"
    assert '--opt_level' in cmd, "Should include opt_level"
    assert '0' in cmd, "opt_level should be 0"
    assert '-c' not in cmd, "Should not include -c (no config)"
    assert '--gen_log' not in cmd, "Should not include --gen_log"
    assert '--aggressive_partitioning' not in cmd, "Should not include --aggressive_partitioning"
    
    print("✅ PASS: Minimal configuration correct\n")


def test_full_configuration():
    """Test command building with all options enabled."""
    print("Test 2: Full Configuration")
    print("-" * 60)
    
    options = {
        'config_path': '/configs/bert.json',
        'opt_level': 1,
        'gen_log': True,
        'aggressive_partitioning': True,
        'compile_input_nodes': 'input_ids,attention_mask',
        'compile_output_nodes': 'logits,embeddings'
    }
    
    executor = DXComExecutor(
        input_path='/models/bert.onnx',
        output_path='/output/bert.dxnn',
        compiler_options=options
    )
    
    cmd = executor._build_command()
    print(f"Generated command: {' '.join(cmd)}")
    
    # Verify
    assert cmd[0] == 'dxcom', "First arg should be 'dxcom'"
    assert cmd[1] == '-m', "Second arg should be '-m' flag"
    assert cmd[2] == '/models/bert.onnx', "Third arg should be input path"
    assert cmd[3] == '-o', "Fourth arg should be '-o' flag"
    assert '-c' in cmd, "Should include -c"
    assert '/configs/bert.json' in cmd, "Should include config path"
    assert '--opt_level' in cmd, "Should include opt_level"
    assert '1' in cmd, "opt_level should be 1"
    assert '--gen_log' in cmd, "Should include --gen_log"
    assert '--aggressive_partitioning' in cmd, "Should include --aggressive_partitioning"
    assert '--compile_input_nodes' in cmd, "Should include input nodes"
    assert 'input_ids,attention_mask' in cmd, "Should include input node names"
    assert '--compile_output_nodes' in cmd, "Should include output nodes"
    assert 'logits,embeddings' in cmd, "Should include output node names"
    
    print("✅ PASS: Full configuration correct\n")


def test_partial_configuration():
    """Test command building with some options enabled."""
    print("Test 3: Partial Configuration")
    print("-" * 60)
    
    options = {
        'config_path': '/configs/mobile.json',
        'opt_level': 1,
        'gen_log': True,
        'aggressive_partitioning': False,  # Disabled
        'compile_input_nodes': '',  # Empty
        'compile_output_nodes': 'output'  # Only output specified
    }
    
    executor = DXComExecutor(
        input_path='/models/mobilenet.onnx',
        output_path='/output/mobilenet.dxnn',
        compiler_options=options
    )
    
    cmd = executor._build_command()
    print(f"Generated command: {' '.join(cmd)}")
    
    # Verify
    assert cmd[0] == 'dxcom', "First arg should be 'dxcom'"
    assert '-c' in cmd, "Should include -c"
    assert '--opt_level' in cmd, "Should include opt_level"
    assert '1' in cmd, "opt_level should be 1"
    assert '--gen_log' in cmd, "Should include --gen_log"
    assert '--aggressive_partitioning' not in cmd, "Should NOT include --aggressive_partitioning"
    assert '--compile_input_nodes' not in cmd, "Should NOT include input nodes (empty)"
    assert '--compile_output_nodes' in cmd, "Should include output nodes"
    assert 'output' in cmd, "Should include output node name"
    
    print("✅ PASS: Partial configuration correct\n")


def test_missing_keys():
    """Test command building handles missing keys gracefully."""
    print("Test 4: Missing Keys (Partial Dict)")
    print("-" * 60)
    
    # Minimal dict - missing some keys
    options = {
        'opt_level': 1,
        'gen_log': True
        # Other keys missing
    }
    
    executor = DXComExecutor(
        input_path='/models/test.onnx',
        output_path='/output/test.dxnn',
        compiler_options=options
    )
    
    # Should not raise exception
    cmd = executor._build_command()
    print(f"Generated command: {' '.join(cmd)}")
    
    # Verify
    assert cmd[0] == 'dxcom', "First arg should be 'dxcom'"
    assert '--opt_level' in cmd, "Should include opt_level"
    assert '--gen_log' in cmd, "Should include --gen_log"
    assert '-c' not in cmd, "Should not include -c (missing key)"
    
    print("✅ PASS: Missing keys handled gracefully\n")


def test_command_format():
    """Test that command format matches specification."""
    print("Test 5: Command Format")
    print("-" * 60)
    
    options = {
        'config_path': '/cfg.json',
        'opt_level': 1,
        'gen_log': True,
        'aggressive_partitioning': False,
        'compile_input_nodes': 'in1,in2',
        'compile_output_nodes': 'out1'
    }
    
    executor = DXComExecutor(
        input_path='input.onnx',
        output_path='output.dxnn',
        compiler_options=options
    )
    
    cmd = executor._build_command()
    cmd_str = ' '.join(cmd)
    print(f"Generated command:\n{cmd_str}")
    
    # Verify format: dxcom -m input.onnx -o output_dir [options]
    assert cmd[0] == 'dxcom', "Should start with dxcom"
    assert cmd[1] == '-m', "Second arg should be '-m' flag"
    assert cmd[2] == 'input.onnx', "Third arg should be input (after -m flag)"
    assert cmd[3] == '-o', "Fourth arg should be '-o' flag"
    assert '-m' in cmd, "Should use -m flag for input"
    assert '-o' in cmd, "Should use -o flag for output"
    
    # Check that format matches: dxcom -m input -o output_dir ...
    expected_start = 'dxcom -m input.onnx -o'
    assert cmd_str.startswith(expected_start), f"Should start with '{expected_start}'"
    
    print(f"✅ PASS: Command format correct (positional args)\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Task 4.2: Command Builder Unit Tests")
    print("=" * 60)
    print()
    
    try:
        test_minimal_configuration()
        test_full_configuration()
        test_partial_configuration()
        test_missing_keys()
        test_command_format()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
